#!/bin/bash

export PYTHONPATH="/home/yhy/EmbeddedFuzzer:/home/yhy/EmbeddedFuzzer/src"
/root/anaconda3/bin/python -m lithium /home/yhy/EmbeddedFuzzer/src/experiment/interesting.py "$1"
rm -rf tmp1
