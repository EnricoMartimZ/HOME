from setuptools import find_packages, setup

package_name = 'pacote_teste'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='emzx',
    maintainer_email='emzx@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'add_two_ints_server = pacote_teste.add_two_ints_server:main',
            'number_publisher = pacote_teste.number_publisher:main',
            'number_counter = pacote_teste.number_counter:main',
            'hw_status_publisher = pacote_teste.hw_status_publisher:main',
            'led_panel = pacote_teste.led:main',
            'battery = pacote_teste.battery:main',
            'noticias = pacote_teste.radio:main',
            'smartphone = pacote_teste.smartphone:main'
        ],
    },
)
