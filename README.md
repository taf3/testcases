## Directory Structure

The current implementation of the testing framework has the following directory structure of testcases repository (only high-level directories are shown):
```
  + testcases
    + config
      - env
      - setup
    + general
    + l2
    + l3
```
## Config

* **env** –  identify devices, setting  environment option. Environment config describes all allowed devices for setups. Which devices will be used in current run is defined in the setup configuration.
* **setup**  –  define environment configuration, senvironment setup option. The env part is a list of devices in the current setup. The cross part is a dictionary with cross ids as the keys and the appropriate list of connections as values.

All configs must be placed in `<tests_root>/config/<env|setup>` directory.

More detail about **setup** and **environment** configuration can be found by the following link: [Setup and Environment config ](https://github.com/IBarna/Create-docs-TAF/wiki/3.-Test-execution-preconfiguration)

## Samples Test Structure

### 1. General

A list of high level samples for a General testing:

* Simple switch device configuration and operations(restart, get).
* ONS switch direct XMLRPC wrappers usage.
* Wrappers for negative scenarios.
* TG operations (configure traffic, start capture, send traffic, get statistics, fragmentation).
* IxNetwork configuration (iface, traffic, LACP, OSPF, BGP).

### LAYER 2 PROTOCOLS:
***

### 2. ACL

A list of high level samples for a ACL testing:

* Verify that simple ACL configuration can be added.
* Verify that simple ACL configuration can be deleted.
* Verify that traffic is processed according to the configured ACLs.
* Verify that ACL Statistics is updated according to the configured ACLs.

### 3. DCBX

A list of high level samples for a DCBX testing:

* Verify that the DUT inhibits the transmission of max_sized frames when a PFC frame is received with quanta value equal to 10000.

### 4. FDB

A list of high level samples for a FDB testing:

* Verify that Static FDB record can be created and deleted.
* Verify that traffic is processed according to the configured static FDB.
* Verify that dynamic FDB record can be created and traffic is processed according to this record.


### 5. IGMP

A list of high level samples for a IGMP testing:

* Verify that a multicast traffic is received only on the port where Group is registered.

### 6. LACP

A list of high level samples for a LACP testing:

* Verify that Dynamic LAG can be created and deleted.
* Verify that port can be added to(removed from) dynamic LAG.
* Verify that correct LACP frames are transmitted from the configured dynamic LAG.

### 7. LAG

A list of high level samples for a LAG testing:

* Verify that static LAG can be created and deleted.
* Verify that port can be added to(removed from) static LAG.
* Verify that traffic is processed according to the configured LAGs.

### 8. Port Mirroring

A list of high level samples for a Port Mirroring testing:

* Verify that simple Mirroring session can be created and deleted.
* Verify that traffic is processed according to the configured Mirroring session.

### 9. Multicast

A list of high level samples for a Multicast testing:

* Verify that multicast record can be added and deleted.
* Verify that multicast traffic is forwarded according to the L2Multicast table.

### 10. Pause Frame

A list of high level samples for a Pause Frame testing:

* Verify that device doesn't flood received pause frames when flow control mode is configured.
* Verify that "RxTx" flow control manages different type of traffic correctly.

### 11. PortConfiguration

A list of high level samples for a Port Configuration testing:

* Verify that port configuration can be changed.

### 12. QinQ

A list of high level samples for a QinQ testing:

* Verify that packet sent without double-tag from one Vlan to another is received on the correct port with double-tag (Vlan Stacking).
* Verify that customer unmapped packet is received on correct port if provider mapped packet from one Vlan to another is send (Using Vlan Mapping).

### 13. QoS

A list of high level samples for a QoS testing:

* Verify that packets with Dot1p higher priority displace packets with Dot1p lower priority by Strict schedule mode.
* Verify that packets with DSCP higher priority displace packets with DSCP lower priority by Strict schedule mode.

### 14. Statistics

A list of high level samples for a Statistics testing:

* Verify that proper Statistics value updated during specific traffic is processed.

### 15. VLAN

A list of high level samples for a Vlan testing:

* Verify that simple Vlan can be created and deleted.
* Verify that port can be added to (removed from) Vlan.
* Verify that traffic is processed according to the configured Vlan.

### LAYER 3 PROTOCOLS:

***

### 16. ARP

A list of high level samples for an ARP testing:

* Verify that ARP configuration can be modified.
* Verify that Static ARP entry can be created and deleted.
* Verify that traffic is processed according to the created Static ARP.
* Verify that Dynamic ARP entry can be learned.
* Verify that traffic is processed according to the learned Dynamic ARP.

### 17. OSPFv2

A list of high level samples for an OSPFv2 testing:

* Verify OSPF hello packet has correct fields after OSPF protocol initialization.
* Verify that Routes table accommodates at least 1k entries using OSPF routes.

### 18. Static Routes

A list of high level samples for a Static Route testing:

* Verify traffic forwarding upon two port on one VLAN and one Router Interface.
* Verify static route behavior upon one port with two VLANs.

## Conftest.py

Local **conftest.py** plugins contain directory-specific hook implementations. Hook Session and test running activities will invoke all hooks defined in **conftest.py** files closer to the root of the filesystem.

* Load necessary plugins from taf/plugins folder
    * **"plugins.pytest_reportingserver"** - reporting functionality
    * **"plugins.pytest_returns"** - returns values instead of PASS
    * **"plugins.pytest_multiple_run"** - execute test cases several times
    * **"plugins.pytest_start_from_case"** - start execution from the specified test
    * **"plugins.pytest_onsenv"** - initialize environment
    * **"plugins.pytest_skip_filter"** - remove skipped tests from run
    * **"plugins.pytest_random_collection"**- execute one test (random) from test suite
* Configure logging functionality

More detail information can be found by the following link: [conftest.py](http://doc.pytest.org/en/latest/writing_plugins.html?highlight=conftest#conftest-py-plugins).

## Pytest.ini

This file contains:
* minimal pytest version required for running tests;
* mandatory command line options;
* information about available registered markers.

More detail information can be found by the following links:
* pytest [Build-in marks](http://doc.pytest.org/en/latest/mark.html#mark);
* pytest [Custom marks](http://doc.pytest.org/en/latest/example/markers.html).

## LICENSE

Apache 2.0. See [LICENSE](https://github.com/taf3/testcases/blob/master/LICENSE) for more details.
