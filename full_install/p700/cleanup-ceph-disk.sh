#!/bin/sh
sudo rm -rf /var/lib/rook
sudo rm -rf /var/lib/kubelet/plugins_registry
for drive in sda sdb sdc sdd sde sdf; do
    echo "Processing /dev/$drive..."

    # 1. Zero out the drive's partition table and signatures (Safe for a second run)
    # sudo wipefs --all --force /dev/$drive

    # 2. Aggressively remove any LVM Physical Volume signatures
    # This resolves issues where the kernel or LVM caches PV metadata.
    # sudo pvremove --force --force /dev/$drive
    sudo ceph-volume lvm zap --destroy /dev/$drive
    
    # 3. Use dd to zero the beginning of the disk (where Ceph/GPT headers live)
    # sudo dd if=/dev/zero of=/dev/$drive bs=1M count=100 oflag=direct status=none
    sudo wipefs --all --force /dev/$drive

    # 4. Clear kernel cache of old partitions
    sudo partprobe /dev/$drive

    echo "/dev/$drive is clean."
done
sudo mkdir -p /var/lib/kubelet/plugins_registry

