Toolset for Generating Multi-hop Topologies for the FIT IoT-LAB
===============================================================

Implementation of the algorithms presented in

F. Kauer and V. Turau, Constructing Customized Multi-hop Topologies in Dense Wireless Network Testbeds in Ad-hoc, Mobile, and Wireless Networks, Lecture Notes in Computer Science 11104, presented at the 17th International Conference on Ad Hoc Networks and Wireless (AdHoc-Now), St Malo, France, September 2018. https://doi.org/10.1007/978-3-030-00247-3_28

Preprint available at https://arxiv.org/abs/1805.06661

Usage
-----

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

    For further options, run `./tree_selection.py --help`.

    It outputs multiple results like this
    ```
    Topology with 6 nodes, depth 2 and root 6 (0xc279) for bound 56:
    [6, 10, 3, 7, 18, 2]
    Graph plot in ./results/lyon-all-01.png
    ```

    That means, a tree topology was found that is also illustrated in the given png file. In this case, it consists of 6 nodes, has a depth of 2 and the node with ID 6 as root. The other nodes are 10, 3, 7, 18, 2. When using these 6 nodes in an IoT-LAB experiment and setting the transmission power and sensitivity according to the bound 56 (see the paper above for details), one can expect the given tree topology.


8. Run the fixed density algorithm 
    ```
    cd ~/topologies/iotlab_topologies/selection/
    ./density.py lyon all 60
    ```

    For further options, run `./density.py --help`.

    The result is similar to the one of the tree selection. However, you have to manually specify the bound (60 in this example).

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
