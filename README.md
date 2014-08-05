Getting started
---------------

* Install [Vagrant](http://vagrantup.com),
  [Fabric](http://fabric.readthedocs.org/en/latest/installation.html),
  and [fabtools](http://fabtools.readthedocs.org/en/latest/).

* Change config.ini to have your project name (currently called
  fab-tools-start-kit).  Only use letters, numbers, hyphens

* From the command line, run `vagrant up`. This will
  create and power up a virtual machine
  
* If needed, modify the time zone in `fabfile\provision.py`

* Run `fab dev provision`. This will install all the necessary packages
  on the virtual machine.

* You can now SSH to the virtual machine with `vagrant ssh`

* The simpleSAMLphp server can be accessed at [http://localhost:8000/simplesamlphp/] 

TODO
----

* Move the time zone choice from `provision.py` to `config.ini`
