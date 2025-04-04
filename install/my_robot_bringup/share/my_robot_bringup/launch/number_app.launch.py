from launch import LaunchDescription
from launch_ros.actions import Node 

def generate_launch_description():
    ld = LaunchDescription()
    

    noticias1 = Node(package="pacote_teste", executable="noticias", name="robot_news_station_giskard", parameters=[{"name": "giskard"}])
    noticias2 = Node(package="pacote_teste", executable="noticias", name="robot_news_station_bb8", parameters=[{"name": "bb8"}])
    noticias3 = Node(package="pacote_teste", executable="noticias", name="robot_news_station_daneel", parameters=[{"name": "daneel"}])
    noticias4 = Node(package="pacote_teste", executable="noticias", name="robot_news_station_lander", parameters=[{"name": "lander"}])
    noticias5 = Node(package="pacote_teste", executable="noticias", name="robot_news_station_c3po", parameters=[{"name": "c3po"}])
    smartphone = Node(package="pacote_teste", executable="smartphone")

    ld.add_action(noticias1)
    ld.add_action(noticias2)
    ld.add_action(noticias3)
    ld.add_action(noticias4)
    ld.add_action(noticias5)
    ld.add_action(smartphone)
    return ld



'''def generate_launch_description():
    ld = LaunchDescription()
    
    remap_number_topic = ("number", "my_number")

    number_publisher_node = Node(package="pacote_teste", executable="number_publisher", remappings=[remap_number_topic], parameters=[{"number_to_publish": 4}, {"publish_frequency": 5.0}])
    number_counter_node = Node(package= "pacote_teste", executable="number_counter", name="my_number_counter")

    ld.add_action(number_publisher_node)
    ld.add_action(number_counter_node)
    return ld'''