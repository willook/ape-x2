#!/bin/bash
tmux new -s replay -d 'source activate RL; python replay.py; read'
tmux new -s learner -d 'source activate RL; REPLAY_IP="127.0.0.1" N_ACTORS=8 python learner.py --cuda; read'
tmux new -s actor0 -d 'source activate RL; REPLAY_IP="127.0.0.1" LEARNER_IP="127.0.0.1" ACTOR_ID=0 N_ACTORS=8 python actor.py; read'
tmux new -s actor1 -d 'source activate RL; REPLAY_IP="127.0.0.1" LEARNER_IP="127.0.0.1" ACTOR_ID=1 N_ACTORS=8 python actor.py; read'
tmux new -s actor2 -d 'source activate RL; REPLAY_IP="127.0.0.1" LEARNER_IP="127.0.0.1" ACTOR_ID=2 N_ACTORS=8 python actor.py; read'
tmux new -s actor3 -d 'source activate RL; REPLAY_IP="127.0.0.1" LEARNER_IP="127.0.0.1" ACTOR_ID=3 N_ACTORS=8 python actor.py; read'
tmux new -s actor4 -d 'source activate RL; REPLAY_IP="127.0.0.1" LEARNER_IP="127.0.0.1" ACTOR_ID=4 N_ACTORS=8 python actor.py; read'
tmux new -s actor5 -d 'source activate RL; REPLAY_IP="127.0.0.1" LEARNER_IP="127.0.0.1" ACTOR_ID=5 N_ACTORS=8 python actor.py; read'
tmux new -s actor6 -d 'source activate RL; REPLAY_IP="127.0.0.1" LEARNER_IP="127.0.0.1" ACTOR_ID=6 N_ACTORS=8 python actor.py; read'
tmux new -s actor7 -d 'source activate RL; REPLAY_IP="127.0.0.1" LEARNER_IP="127.0.0.1" ACTOR_ID=7 N_ACTORS=8 python actor.py; read'

#tmux new -s evaluator -d 'source activate RL; LEARNER_IP="127.0.0.1" python eval.py; read'
