### 1. Generate a SSH key in Remote server for SSH Access

```bash
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"
```

### 2. Copy public key and upload into https://github.com/settings/keys:

```bash
cd ~/.ssh
# Copy all the output
cat id_rsa.pub
```

3. Click 'New SSH Key' in https://github.com/settings/keys and paste the text into the content.

4. Config git user in terminal (your server):

```bash
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```

