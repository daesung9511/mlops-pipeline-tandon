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

### 3. Check out to other git branches

To check out the remote branch `Training` (which exists as `origin/Training`) and create a corresponding local branch, follow these steps:

1. Fetch the latest remote branches
This ensures your local repository is aware of all branches on the remote.

```bash
git fetch origin
```

This step is optional if you already see `origin/Training` in `git branch -r`, but it's good practice to ensure you have the latest refs.


2. Create and switch to the local branch from the remote.

```bash
git checkout -b Training origin/Training
```
    
This creates a new local branch named `Training` that tracks the remote branch `origin/Training` and switches you to it.
    
Alternatively, with newer versions of Git (2.23+), you can use:

```bash
git switch -c Training origin/Training
```

This achieves the same result.