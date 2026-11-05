#!/usr/bin/env python3
"""Back up every MTD partition of a Teltonika RUT9xx over SSH and verify each one by MD5."""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys

SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no",
    "-o", "UserKnownHostsFile=/dev/null",
    "-o", "HostKeyAlgorithms=+ssh-rsa",
    "-o", "PubkeyAcceptedKeyTypes=+ssh-rsa",
    "-o", "KexAlgorithms=+diffie-hellman-group14-sha1",
]
FULL_IMAGE_ORDER = ["u-boot", "config", "art", "firmware", "event-log"]
FLASH_SIZE = 16 * 1024 * 1024


def ssh_cmd(host, remote):
    base = ["ssh", *SSH_OPTS, f"root@{host}", remote]
    if os.environ.get("SSHPASS"):
        if not shutil.which("sshpass"):
            sys.exit("SSHPASS is set but sshpass is not installed")
        base = ["sshpass", "-e", *base]
    return base


def run(host, remote):
    return subprocess.run(ssh_cmd(host, remote), capture_output=True, text=True).stdout.strip()


def read_mtd(host):
    parts = []
    for line in run(host, "cat /proc/mtd").splitlines()[1:]:
        dev, size, _erase, name = line.split(maxsplit=3)
        parts.append((dev.rstrip(":"), int(size, 16), name.strip('"')))
    if not parts:
        sys.exit("could not read /proc/mtd")
    return parts


def dump(host, outdir, dev, size, name):
    path = os.path.join(outdir, f"{dev}_{name}.bin")
    md5 = hashlib.md5()
    total = 0
    proc = subprocess.Popen(ssh_cmd(host, f"dd if=/dev/{dev}ro bs=64k 2>/dev/null"),
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    with open(path, "wb") as f:
        while chunk := proc.stdout.read(65536):
            f.write(chunk)
            md5.update(chunk)
            total += len(chunk)
    proc.wait()
    remote = run(host, f"md5sum /dev/{dev}ro").split()[0:1]
    ok = total == size and remote == [md5.hexdigest()]
    print(f"{dev:6} {name:12} {total:>10} B  {'OK' if ok else 'MISMATCH'}")
    return path, ok


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("outdir")
    ap.add_argument("--host", default="192.168.1.1")
    ap.add_argument("--keep-logging", action="store_true",
                    help="do not pause the RutOS event logger while reading (event-log may then mismatch)")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    parts = read_mtd(args.host)
    if not args.keep_logging:
        run(args.host, "killall eventslogd logtrigger port_event_checker 2>/dev/null; sync")

    files, all_ok = {}, True
    try:
        for dev, size, name in parts:
            path, ok = dump(args.host, args.outdir, dev, size, name)
            files[name] = path
            all_ok &= ok
    finally:
        if not args.keep_logging:
            run(args.host, "/etc/init.d/eventslog restart 2>/dev/null; /etc/init.d/log restart 2>/dev/null")

    if all(n in files for n in FULL_IMAGE_ORDER):
        full = os.path.join(args.outdir, "full_flash_16MB.bin")
        with open(full, "wb") as out:
            for n in FULL_IMAGE_ORDER:
                with open(files[n], "rb") as f:
                    shutil.copyfileobj(f, out)
        size = os.path.getsize(full)
        print(f"full flash image: {full} ({size} B){'' if size == FLASH_SIZE else '  UNEXPECTED SIZE'}")
        all_ok &= size == FLASH_SIZE

    print("all partitions verified" if all_ok else "SOME PARTITIONS DID NOT VERIFY")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
