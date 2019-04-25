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

4. Clone this repository and install the prerequisites

    ```
    git clone https://github.com/koalo/iotlab_topologies ~/topologies/iotlab_topologies
    sudo apt-get install graphviz-dev python3-tk graphviz
    pip3 install pygraphviz networkx pulp numpy scipy matplotlib pandas
    ```

5. Run a channel evaluation measurement and wait until it is finished

    ```
    cd ~/topologies/iotlab_topologies/measurement/
    ./run.py lyon
    ```

6. Analyze the logs

    ```
    cd ~/topologies/iotlab_topologies/topology/
    ./generate_paths_data.py lyon m3 all ../measurement/logs/latest/*_run.log
    ./linkhist.py paths-data-lyon-m3-all.json
    ./nodedeg.py paths-data-lyon-m3-all.json
    ```

7. Run the tree selection algorithm
    ```
    cd ~/topologies/iotlab_topologies/selection/
    ./tree_selection.py lyon all
    ```

8. Run the fixed density algorithm 
    ```
    cd ~/topologies/iotlab_topologies/selection/
    ./density.py lyon all 60
    ```

Generate the Measurement Firmware
---------------------------------

Instead of using the precompiled firmware files as described above, you can compile the measurement firmware. This gives for example the possibility to change the radio channel (have a look at the run.py for that). Attention: There currently seems to be a bug with some compiler versions where the firmware seems to have been built correctly, but it does not run properly. If this is the case for you, please create an issue.

    sudo apt-get install scons gcc-arm-none-eabi
    git clone https://github.com/CometOS/CometOS.git ~/topologies/cometos
    echo 'export COMETOS_PATH=~/topologies/cometos' >> ~/.bashrc
    echo 'export PATH=$PATH:$COMETOS_PATH/support/builder' >> ~/.bashrc
    source ~/.bashrc
    cd ~/topologies/iotlab_topologies/cometos/
    ./run.py lyon
    cd ~/topologies/iotlab_topologies/topology/
    ./generate_paths_data.py lyon m3 all ../cometos/logs/latest/*_run.log
    ...
