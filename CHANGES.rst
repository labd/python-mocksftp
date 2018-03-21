Version 1.0.1 (2018-03-21)
==========================

* Fix ``remove()`` call for directories.


Version 1.0 (2018-03-21)
========================

* Added ``remove()``, ``chmod()``, ``chown()``, ``symlink()``, ``utime()`` support.
* Addded check to avoid breaking outside the SFTP server root.


Version 0.2.0 (2017-08-22)
==========================

* Added ``lstat()``, ``rename()``, ``posix_rename()`` and ``readlink()`` support.
* Fixed ``stat()`` to return the symlink data instead of the target file.


Version 0.1.0 (2017-06-26)
==========================

* Initial release, forked from https://github.com/carletes/mock-ssh-server
