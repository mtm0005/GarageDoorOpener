# Connect to wi-fi
# git clone repository
# Run this script

# checkout alpha branch
git checkout alpha
git pull

# Install required modules
list_of_modules="firebase
PyDrive
pyfcm
RPi.GPIO"

for module in $list_of_modules
do
    sudo pip3 install $module
done

# modify crontab
echo '*/5 * * * * ~/git/GarageDoorOpener/cronjob.sh' | crontab -