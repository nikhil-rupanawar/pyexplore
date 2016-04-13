

# pyexplore

Script scans for given modules/classes/function/object
And provides useful info at STATIC time , in json or dict formats
	 - functions and there arguments , doc
	 - classes and there methods, doc
         - global variables and symbols with values
         - imported modules and symbols from that modules and source paths

											
									
# Prerequisites:
         - python 2.7
         - set your PYTHONPATH or sys.path correctly 
           so that packages or modules are searchable in given path
		   
# Run as below examples :
   python explore.py paramiko
   python explore.py paramiko.sftp_client
   python explore.py paramiko.sftp_client
   python explore.py paramiko.sftp_client.SFTPClient
   python explore.py paramiko.sftp_client._to_unicode
   python explore.py paramiko.sftp_client.b_slash
   python explore.py /usr/local/lib/python2.7/dist-packages/paramiko/sftp_client.pyc
   python explore.py /usr/local/lib/python2.7/dist-packages/paramiko/sftp_client.py
   python explore.py /root/myfiles/test.py
   
# Use as module:
   from pyexplore import explore
   result_dict = explore('paramiko')
   
   
# Output:
       When you run it from json dumped on console
       When you call main funtion
