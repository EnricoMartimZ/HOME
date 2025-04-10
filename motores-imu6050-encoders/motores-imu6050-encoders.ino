#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_MPU6050.h>

Adafruit_MPU6050 mpu; // Instancia o sensor

// Declara as variáveis do sensor
float aX = 0;
float aY = 0;
float aZ = 0;
float gX = 0;
float gY = 0;
float gZ = 0;

// Pinos de controle para o motor 1
int motor1Pin1 = 18; 
int motor1Pin2 = 19; 
int enable1Pin = 32;

// Pinos do encoder para o motor 1
const int encoder1PinA = 4;
const int encoder1PinB = 15;

// Pinos de controle para o motor 2
int motor2Pin1 = 14;  // Ajuste conforme sua configuração
int motor2Pin2 = 12;  // Ajuste conforme sua configuração
int enable2Pin = 23;  // Ajuste conforme sua configuração

// Pinos do encoder para o motor 2
const int encoder2PinA = 2;  // Ajuste conforme sua configuração
const int encoder2PinB = 13;  // Ajuste conforme sua configuração

// Variáveis para odometria de cada motor
volatile long pulseCount1 = 0;
volatile long pulseCount2 = 0;
const int pulsesPerRevolution = 330;  // 11 pulsos * razão de redução 30:1
float revolutions1 = 0.0;
float revolutions2 = 0.0;
int direction1 = 1;  // 1: sentido horário, -1: sentido anti-horário
int direction2 = 1;  // 1: sentido horário, -1: sentido anti-horário

// Configurações de tempo e velocidade
const int MOTOR_RUN_TIME = 60000;    // 1 minuto em milissegundos
const int MOTOR_PAUSE_TIME = 15000;  // 15 segundos em milissegundos
const int MOTOR_DUTY_CYCLE = 80;     // 80% do ciclo de trabalho

// Variáveis para debounce
unsigned long lastDebounceTime1 = 0;
unsigned long lastDebounceTime2 = 0;
const unsigned long debounceDelay = 1; // milissegundos (ajuste conforme necessário)

// Filtro de média móvel para RPM
const int filterSize = 5; // Tamanho do filtro
float rpm1Filter[filterSize] = {0};
float rpm2Filter[filterSize] = {0};
int filterIndex = 0;

// Variáveis para detecção de outliers
const float maxRPMChange = 50.0; // Mudança máxima permitida de RPM entre leituras
float lastValidRPM1 = 0.0;
float lastValidRPM2 = 0.0;

// Estrutura para filtro de Kalman
struct KalmanFilter {
  float q; // Processo de ruído
  float r; // Ruído de medição
  float x; // Valor estimado
  float p; // Estimativa de erro
  float k; // Ganho de Kalman
};

KalmanFilter rpm1Kalman = {0.01, 0.1, 0.0, 1.0, 0.0};
KalmanFilter rpm2Kalman = {0.01, 0.1, 0.0, 1.0, 0.0};

// Funções de interrupção para os encoders com debounce
void IRAM_ATTR handleEncoder1() {
  // Verificar tempo desde último pulso para evitar bouncing
  unsigned long currentTime = micros();
  if ((currentTime - lastDebounceTime1) < debounceDelay*1000) {
    return; // Ignorar pulsos muito próximos
  }
  lastDebounceTime1 = currentTime;
  
  // Método para determinar direção
  int b = digitalRead(encoder1PinB);
  if (digitalRead(encoder1PinA) == HIGH) {
    if (b == LOW) {
      pulseCount1++;  // Sentido horário
      direction1 = 1;
    } else {
      pulseCount1--;  // Sentido anti-horário
      direction1 = -1;
    }
  }
}

void IRAM_ATTR handleEncoder2() {
  // Verificar tempo desde último pulso para evitar bouncing
  unsigned long currentTime = micros();
  if ((currentTime - lastDebounceTime2) < debounceDelay*1000) {
    return; // Ignorar pulsos muito próximos
  }
  lastDebounceTime2 = currentTime;
  
  // Método para determinar direção
  int b = digitalRead(encoder2PinB);
  if (digitalRead(encoder2PinA) == HIGH) {
    if (b == LOW) {
      pulseCount2++;  // Sentido horário
      direction2 = 1;
    } else {
      pulseCount2--;  // Sentido anti-horário
      direction2 = -1;
    }
  }
}

// Função para aplicar média móvel
float applyMovingAverage(float newValue, float* filterArray) {
  // Adicionar novo valor ao array
  filterArray[filterIndex] = newValue;
  filterIndex = (filterIndex + 1) % filterSize;
  
  // Calcular média
  float sum = 0;
  for (int i = 0; i < filterSize; i++) {
    sum += filterArray[i];
  }
  return sum / filterSize;
}

// Função para verificar outliers
float checkOutlier(float newRPM, float lastRPM) {
  if (lastRPM == 0.0) {
    return newRPM; // Primeira leitura
  }
  
  if (abs(newRPM - lastRPM) > maxRPMChange) {
    return lastRPM; // Outlier detectado, manter valor anterior
  }
  
  return newRPM; // Valor aceito
}

// Aplicar filtro de Kalman
float applyKalman(float measurement, KalmanFilter* filter) {
  // Predição
  filter->p = filter->p + filter->q;
  
  // Atualização
  filter->k = filter->p / (filter->p + filter->r);
  filter->x = filter->x + filter->k * (measurement - filter->x);
  filter->p = (1 - filter->k) * filter->p;
  
  return filter->x;
}

void setup() {
  // Configurar pinos do motor 1
  pinMode(motor1Pin1, OUTPUT);
  pinMode(motor1Pin2, OUTPUT);
  pinMode(enable1Pin, OUTPUT);
  
  // Configuração do encoder do motor 1
  pinMode(encoder1PinA, INPUT_PULLUP);
  pinMode(encoder1PinB, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(encoder1PinA), handleEncoder1, RISING);
  
  // Configurar pinos do motor 2
  pinMode(motor2Pin1, OUTPUT);
  pinMode(motor2Pin2, OUTPUT);
  pinMode(enable2Pin, OUTPUT);
  
  // Configuração do encoder do motor 2
  pinMode(encoder2PinA, INPUT_PULLUP);
  pinMode(encoder2PinB, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(encoder2PinA), handleEncoder2, RISING);
  
  // Configuração do IMU:

  // Configura os pinos I2C (SDA, SCL):
  Wire.begin(21, 22); // Ajuste os pinos conforme necessário. Recomendamos 21 e 22 para o ESP32, mas pode variar de acordo com o modelo. Use o código scanner I2C para verificar os pinos corretos. Ele está disponível no final deste arquivo.

  // Inicializa o sensor
  if (!mpu.begin()) {
    Serial.println("Falha ao inicializar o sensor MPU6050. Verifique as conexões.");
    while (1) {
      delay(10);
    }
  }

  // Configura o sensor
  mpu.setAccelerometerRange(MPU6050_RANGE_16_G);
  mpu.setGyroRange(MPU6050_RANGE_250_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

  Serial.begin(115200);
  Serial.println("Controle de dois motores com odometria e filtros");
  Serial.println("1 minuto rodando - 15 segundos parado - Inversão de sentido");
}

void printOdometry() {
  // Calcular rotações para cada motor
  revolutions1 = (float)pulseCount1 / pulsesPerRevolution;
  revolutions2 = (float)pulseCount2 / pulsesPerRevolution;

  delay(200);
  
  Serial.println("Odometria dos Motores:");
  Serial.print("Motor 1 - Pulsos: ");
  Serial.print(pulseCount1);
  Serial.print(" | Rotações: ");
  Serial.print(revolutions1, 2);
  Serial.print(" | Direção: ");
  Serial.println((direction1 == 1) ? "Horário" : "Anti-horário");

  delay(200);
  
  Serial.print("Motor 2 - Pulsos: ");
  Serial.print(pulseCount2);
  Serial.print(" | Rotações: ");
  Serial.print(revolutions2, 2);
  Serial.print(" | Direção: ");
  Serial.println((direction2 == 1) ? "Horário" : "Anti-horário");

  delay(200);

  Serial.print("Acelerometro: ");
  Serial.print(aX);
  Serial.print(", ");
  Serial.print(aY);
  Serial.print(", ");
  Serial.print(aZ);
  Serial.print(" | Giroscopio: ");
  Serial.print(gX);
  Serial.print(", ");
  Serial.print(gY);
  Serial.print(", ");
  Serial.println(gZ);
}

void runMotors(bool forward, int dutyCycle, unsigned long runTime) {
  // Configurar direção dos motores
  if (forward) {
    // Motor 1 - sentido horário
    digitalWrite(motor1Pin1, LOW);
    digitalWrite(motor1Pin2, HIGH);
    
    // Motor 2 - sentido horário
    digitalWrite(motor2Pin1, LOW);
    digitalWrite(motor2Pin2, HIGH);

    delay(200);
    
    Serial.println("Iniciando motores no sentido HORÁRIO");

    delay(200);
  } else {
    // Motor 1 - sentido anti-horário
    digitalWrite(motor1Pin1, HIGH);
    digitalWrite(motor1Pin2, LOW);
    
    // Motor 2 - sentido anti-horário
    digitalWrite(motor2Pin1, HIGH);
    digitalWrite(motor2Pin2, LOW);
    
    delay(200);
    Serial.println("Iniciando motores no sentido ANTI-HORÁRIO");
    delay(200);
  }
  
  // Limitar ciclo de trabalho entre 0 e 100%
  dutyCycle = constrain(dutyCycle, 0, 100);
  
  // Resetar contadores para este ciclo
  long startingPulseCount1 = pulseCount1;
  long startingPulseCount2 = pulseCount2;
  
  // Aplicar PWM para controle de velocidade
  int pwmValue = map(dutyCycle, 0, 100, 0, 255);
  
  analogWrite(enable1Pin, pwmValue);
  analogWrite(enable2Pin, pwmValue);
  
  Serial.print("Motores rodando a ");
  Serial.print(dutyCycle);
  Serial.println("% de velocidade");
  
  // Tempo de início
  unsigned long startTime = millis();
  unsigned long lastPrintTime = startTime;
  
  // Executar por tempo especificado
  while (millis() - startTime < runTime) {
    // Atualizar informações a cada 10 segundos
    if (millis() - lastPrintTime > 10000) {
      Serial.print("Tempo de execução: ");
      Serial.print((millis() - startTime) / 1000);
      Serial.println(" segundos");
      delay(200);
      printOdometry();
      delay(200);
      lastPrintTime = millis();
    }
    
    // Pequeno delay para não sobrecarregar o processador
    delay(100);
  }
  
  // Calcular RPM para cada motor
  unsigned long elapsedTimeSeconds = runTime / 1000.0;
  long totalPulses1 = abs(pulseCount1 - startingPulseCount1);
  long totalPulses2 = abs(pulseCount2 - startingPulseCount2);
  
  float rawRPM1 = (totalPulses1 / (float)pulsesPerRevolution) * (60.0 / elapsedTimeSeconds);
  float rawRPM2 = (totalPulses2 / (float)pulsesPerRevolution) * (60.0 / elapsedTimeSeconds);
  
  // Aplicar filtragem aos valores de RPM
  // 1. Verificar outliers
  rawRPM1 = checkOutlier(rawRPM1, lastValidRPM1);
  rawRPM2 = checkOutlier(rawRPM2, lastValidRPM2);
  
  // 2. Aplicar filtro de média móvel
  float smoothedRPM1 = applyMovingAverage(rawRPM1, rpm1Filter);
  float smoothedRPM2 = applyMovingAverage(rawRPM2, rpm2Filter);
  
  // 3. Aplicar filtro de Kalman para maior precisão
  float finalRPM1 = applyKalman(smoothedRPM1, &rpm1Kalman);
  float finalRPM2 = applyKalman(smoothedRPM2, &rpm2Kalman);
  
  // Atualizar os últimos valores válidos
  lastValidRPM1 = rawRPM1;
  lastValidRPM2 = rawRPM2;
  
  // Exibir informações finais deste ciclo
  Serial.println("Ciclo finalizado:");
  Serial.print("Motor 1 - Pulsos: ");
  Serial.print(totalPulses1);
  Serial.print(" | RPM bruto: ");
  Serial.print(rawRPM1, 2);
  Serial.print(" | RPM filtrado: ");
  Serial.println(finalRPM1, 2);
  
  Serial.print("Motor 2 - Pulsos: ");
  Serial.print(totalPulses2);
  Serial.print(" | RPM bruto: ");
  Serial.print(rawRPM2, 2);
  Serial.print(" | RPM filtrado: ");
  Serial.println(finalRPM2, 2);
  
  // Exibir odometria total
  delay(200);
  printOdometry();
  delay(200);
}

void stopMotors(unsigned long pauseTime) {
  Serial.println("Parando os motores");
  
  // Parar motor 1
  digitalWrite(enable1Pin, LOW);
  digitalWrite(motor1Pin1, LOW);
  digitalWrite(motor1Pin2, LOW);
  
  // Parar motor 2
  digitalWrite(enable2Pin, LOW);
  digitalWrite(motor2Pin1, LOW);
  digitalWrite(motor2Pin2, LOW);
  
  Serial.print("Aguardando ");
  Serial.print(pauseTime / 1000);
  Serial.println(" segundos");
  
  // Tempo de início
  unsigned long startTime = millis();
  
  // Aguardar pelo tempo especificado - corrigido o problema anterior onde estava comentado
  while (millis() - startTime < pauseTime) {
    delay(100);
  }
  
  Serial.println("Pausa finalizada");
}

void loop() {

  // Recebe os dados do sensor
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  aX = a.acceleration.x;
  aY = a.acceleration.y;
  aZ = a.acceleration.z;
  gX = g.gyro.x;
  gY = g.gyro.y;
  gZ = g.gyro.z;


  static bool currentDirection = true;  // Começa no sentido horário
  
  Serial.println("\n\n========= INICIANDO NOVO CICLO =========");
  
  // Rodar motores na direção atual
  runMotors(currentDirection, MOTOR_DUTY_CYCLE, MOTOR_RUN_TIME);
  
  // Parar motores pelo tempo especificado
  stopMotors(MOTOR_PAUSE_TIME);
  
  // Inverter direção para o próximo ciclo
  currentDirection = !currentDirection;
}