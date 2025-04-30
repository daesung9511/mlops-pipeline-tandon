# Why do we want to change SSH configuration?

When we access Chameleon cloud remote server through terminal, it disconnects if there is no interaction even for a few minutes. Yes, we can reconnect to it using ssh command, pressing ↑ and find the previous command, and then run it (additionally entering a passphrase if you didn't leave it empty). However, this may be cumbersome. Instead, we can set up the wait time for SSH disconnection longer.

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


### Solution 3

In my case, neither solution 1 nor solution 2 did work.
Instead, try configuring YOUR OWN ssh config:

```bash
# On LOCAL machine
nano ~/.ssh/config
```


```bash
Host chameleon-*
    Hostname <your-floating-ip>
    User cc
    IdentityFile ~/.ssh/id_rsa_chameleon_group** # Replace it with your own key name
    ServerAliveInterval 60    # 1-minute client keepalives
    ServerAliveCountMax 30    # 30min total timeout
    TCPKeepAlive yes
```