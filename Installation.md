_Installation instructions for the XBMC-Favorites Installer_



# Introduction #

This plugin enables you to download a personal selection of XBMX plugins,skins and scripts without the need to upload it to your XBMC installation with FTP. The "scripts" directory contains a file "autoexec.py" which is used to autostart the veohproxy script on XBMC startup.
! SO ONLY DOWNLOAD IT IF YOU USE THE VEOHPROXY SCRIPT !.

I've only tested the script on the XBOX. I have no idea if it will work on the Windows/OSX/Linux version of XBMC.

I will try to keep the SVN as up to date as possible.




# XBOX Installation Instructions #

  * Download the "XBMC-Favorites Installer" plugin from this site ("Downloads" section) and upack the archive (you can use winrar -> http://www.rarlab.com)
  * Make sure FTP is enabled in XBMC. You can find this option in "settings/Network/Servers"
  * Find out what the IP address of your XBOX is. You can do this by selecting "settings" on your home screen in the Project Mayhem III skin. On the right side of the home screen you'll fin "Ip Address: xx.xx.xx.xx". Where "xx.xx.xx.xx" is your XBOX ip address.
  * Open Windows Explorer (My Computer) or use your favorite FTP client. I'll only elaborate on Windows Explorer here.
  * Enter "[ftp://YOUR_XBOX_IP_HERE](ftp://YOUR_XBOX_IP_HERE)" in the address bar and press "Enter"
  * You will be prompted a login dialog. The default username and password are **xbox**
  * Copy the "XBMC-Favorites Installer" directory you've extracted before to "E/XBMC/plugins/programs/"
  * The rest is best explained by  [this video](http://xbmc-favorites.googlecode.com/files/HOWTO_install_a_plugin.swf). Open the .swf file with your browser (Firefox i.a.) and make sure you have Flash Player installed.