# Live Logs
sudo journalctl -u vending-machine -f

# Machine restart
sudo systemctl restart vending-machine


# check browser from remote desktop
open http://100.115.208.115:5000
# from the pi
curl -s http://localhost:5000