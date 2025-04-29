### Reference
Link: https://www.perplexity.ai/search/i-am-using-a-chameleon-cloud-i-Rd6EG0eHTOykThcdZFLGMA#1

### Solution 1

```bash
sudo vi /etc/ssh/sshd_config
```

Add or modify these lines, meaning the client will wait 5 minutes (300 seconds) for max three times:

```bash
# Customize the time
ClientAliveInterval 300
ClientAliveCountMax 3
```

Restart ssh service to apply the change.  `sshd` doesn't seem to be installed in Chameleon instance.

```bash
sudo systemctl restart ssh
```

### Solution 2
If solution 1 doesn't work, then open the SSH daemon config file:

```bash
vi ~/.ssh/config
```
    
Add or modify these lines:

```bash
Host * 
  ServerAliveInterval 600
  ServerAliveCountMax 5
```

Again, restart ssh service to apply the change.

```bash
sudo systemctl restart ssh
```