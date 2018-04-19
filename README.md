Toolset for Generating Multi-hop Topologies for the FIT IoT-LAB
===============================================================


1. Setup a working directory

    ```
    mkdir ~/topologies/
    ```

2. Install the IoT-LAB CLI tools (also for Python 3)
	
    https://github.com/iot-lab/iot-lab/wiki/CLI-Tools-Installation

    ```
    cd cli-tools-[release_version] && sudo python3 setup.py install
    ```

3. Authenticate to the IoT-LAB locally and at the IoT-LAB site
   
    ```
    iotlab-auth -u [your_username]
    ssh -tt [your_username]@lyon.iot-lab.info "iotlab-auth -u [your_username]"
    ```

5. Install CometOS for taking the path measurements

    ```
    sudo apt-get install scons gcc-arm-none-eabi
    git clone https://github.com/CometOS/CometOS.git ~/topologies/cometos
    echo 'export COMETOS_PATH=~/topologies/cometos' >> ~/.bashrc
    echo 'export PATH=$PATH:$COMETOS_PATH/support/builder' >> ~/.bashrc
    source ~/.bashrc

    ```

6. Clone this repository and install the prerequisites

    ```
    git clone https://github.com/koalo/iotlab_topologies ~/topologies/iotlab_topologies
    sudo apt-get install graphviz-dev
    pip3 install pygraphviz networkx pulp
    ```

7. Run a channel evaluation measurement and wait until it is finished

    ```
    cd ~/topologies/iotlab_topologies/cometos/
    ./run.py lyon
    ```

8. Analyze the logs

    ```
    cd ~/topologies/iotlab_topologies/topology/
    ./generate_paths_data.py lyon m3 all ../cometos/logs/latest/*_run.log
    ./linkhist.py paths-data-lyon-m3-all.json
    ./nodedeg.py paths-data-lyon-m3-all.json
    ```

9. Run the selection algorithm
    ```
    cd ~/topologies/iotlab_topologies/selection/
    ./selection.py lyon all
    ```

