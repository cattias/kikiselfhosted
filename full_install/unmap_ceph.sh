#!/bin/bash
# Unmap all RBD (Ceph) devices to prevent the kernel from hanging during shutdown
echo "Unmapping Ceph RBD devices..."
for dev in /dev/rbd*; do
    if [ -b "$dev" ]; then
        echo "Unmapping $dev"
        rbd unmap "$dev" || true
    fi
done