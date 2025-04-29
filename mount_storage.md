### 1. Download `rclone`

```bash
curl https://rclone.org/install.sh | sudo bash
```

### 2. Make sure user_allow_other is un-commented in /etc/fuse.conf

```
sudo sed -i '/^#user_allow_other/s/^#//' /etc/fuse.conf
```

### 3. Set up for rclone file

```bash
mkdir -p ~/.config/rclone
nano  ~/.config/rclone/rclone.conf
```

### 4. To configure rclone config file, replace APP_CRED_ID and APP_CRED_SECRET with your own ID and SECRET into the fololowing text

```bash
[chi_tacc]
type = swift
user_id = YOUR_USER_ID
application_credential_id = APP_CRED_ID
application_credential_secret = APP_CRED_SECRET
auth = https://chi.tacc.chameleoncloud.org:5000/v3
region = CHI@TACC
```

Use Ctrl+O and Enter to save the file, and Ctrl+X to exit `nano`.

### 5. For test, run on node-persist

```bash
rclone lsd chi_tacc:
export RCLONE_CONTAINER=object-persist-project25
```

###  6. Make target directory in local

```bash
sudo mkdir -p ~/mnt
sudo chown -R cc ~/mnt
sudo chgrp -R cc ~/mnt
```

### 7. run on node-persist

```bash
rclone mount chi_tacc:object-persist-project25 ~/mnt --read-only --allow-other --daemon
```


### FYI: Why You Can't Write to the Mounted Folder

I wanted to copy files from `~/mlops-pipeline-tandon/models/whisper/` into a mounted directory (`~/mnt/models/whisper/`), but the rclone mount was started with the `--read-only` flag:

```bash
rclone mount chi_tacc:object-persist-project25 /mnt --read-only --allow-other --daemon
```

This makes the mountpoint and all its subdirectories read-only at the OS level, so you cannot create new directories or copy files directly into `/mnt/object` (or `/mnt/models/`) using regular filesystem commands or even rclone copy commands targeting the mountpoint.

- The `--read-only` flag on `rclone mount` makes the entire mountpoint read-only, so any attempts to create folders or copy files into `/mnt/object` (or any subdirectory) will fail with a permissions error.
- This is enforced at the FUSE/filesystem layer, not just by rclone, so even root or sudo cannot override this at the mountpoint.

### Then How can I create a folder and write files into mount storage?

Solution: use `rclone copy`  command.

You do **not** need the mount to be writable to upload files to the remote storage. Instead, use `rclone copy` to send files directly to the remote backend (e.g., TACC object storage), not to the mounted path.

Exmaple:
```bash
rclone copy ~/mlops-pipeline-tandon/models/whisper chi_tacc:$RCLONE_CONTAINER/models/whisper \
    --progress \
    --transfers=32 \
    --checkers=16 \
    --multi-thread-streams=4 \
    --fast-list
```

