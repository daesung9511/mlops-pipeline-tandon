### 1. Download `rclone`

```bash
curl https://rclone.org/install.sh | sudo bash
```

### 2. Make sure user_allow_other is un-commented in /etc/fuse.conf

```
sudo sed -i '/^#user_allow_other/s/^#//' /etc/fuse.conf
```

### 3. Set up rclone config file

```bash
mkdir -p ~/.config/rclone
nano  ~/.config/rclone/rclone.conf
```

### 4. To configure rclone config file, replace APP_CRED_ID and APP_CRED_SECRET with your own ID and SECRET into the fololowing text

When you replace `APP_CRED_ID` and `APP_CRED_SECRET`, **you need to take out double quotation mark ""**.

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

### 5. For test, run `rclone lsd`

If you run this command, you will be able to see a list of mountable object storages in `chi_tacc:`.
```bash
rclone lsd chi_tacc:
```

###  6. Create a mount directory and change permission

It seems like if you try to directly mount `/mnt` directory, it returns the following error message:

```bash
2025/04/30 01:49:25 ERROR : Daemon timed out. Failed to terminate daemon pid 8711: os: process already finished 2025/04/30 01:49:25 CRITICAL: Fatal error: daemon exited with error code 1
```
So I recommend to make a sub-directory under `/mnt` like this. Also, because `/mnt` has by default read-only access, you need to change the permission:
```bash
sudo mkdir -p /mnt/object
sudo chown -R cc /mnt/object
sudo chgrp -R cc /mnt/object
```

### 7. Finally, mount it

```bash
# Export environment variable. Set your own persistent storage name in the variable.
export RCLONE_CONTAINER=object-persist-project25

rclone mount chi_tacc:$RCLONE_CONTAINER /mnt/object --read-only --allow-other --daemon
```


### FYI: Why You Can't Directly Write to the Mounted Directory

I wanted to copy files from `~/mlops-pipeline-tandon/models/whisper/` into a mounted directory (`/mnt/objects/models/whisper/`) using `cp` command. 
However, this is impossible. Here's why:

```bash
rclone mount chi_tacc:object-persist-project25 /mnt --read-only --allow-other --daemon
```

rclone mount was started with the `--read-only` flag. This makes the mount point and all its subdirectories read-only at the OS level, so you cannot create new directories or copy files directly into `/mnt/object` (or `/mnt/models/`) using regular filesystem commands or even rclone copy commands targeting the mount point.

- The `--read-only` flag on `rclone mount` makes the entire mount point read-only, so any attempts to create folders or copy files into `/mnt/object` (or any subdirectory) will fail with a permissions error.
- This is enforced at the FUSE/filesystem layer, not just by rclone, so even root or sudo cannot override this at the mount point.

### Then how can I create a folder and write files into the mounted directory?

Solution: use `rclone copy`  command.

You do **not** need the mount to be writable to upload files to the remote storage. Instead, use `rclone copy` to send files directly to the remote backend (e.g., TACC object storage), not to the mounted path.

Exmaple:
```bash
rclone copy ~/mlops-pipeline-tandon/models/whisper chi_tacc:$RCLONE_CONTAINER/target/directory \
    --progress \
    --transfers=32 \
    --checkers=16 \
    --multi-thread-streams=4 \
    --fast-list
```

You can also copy files from mounted directory into your local, using the same command. `rclone copy` is (almost) always faster than just using `cp` command.

### How to Un-mount

Run this command:
```bash
# Replace `/mnt/object` with your own mounted directory
fusermount -u /mnt/object
```

However, it is very likey to return this failure message:

```bash
fusermount: failed to unmount /home/cc/mnt: Device or resource busy 
```

That is because some user is inside the mount directory! Just `cd` out of current mount directory.
