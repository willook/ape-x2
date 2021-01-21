#!/bin/bash
tmux new 'REPLAY_IP="127.0.0.1" LEARNER_IP="127.0.0.1" ACTOR_ID=0 N_ACTORS=8 python actor.py'
