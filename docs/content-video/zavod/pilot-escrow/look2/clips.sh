C="She does not speak, her mouth stays closed. She moves like a fashion model: graceful, feminine, unhurried, shoulders back, hair moving lightly. Photorealistic, physically correct natural motion, no cuts, no morphing. No text, no captions, no subtitles, no logos. Ambient sound only, no music."
W="The camera slowly tracks backward on a gimbal, keeping her the same size in the frame and the empty space above her head."
S="She stays in place, both feet planted, she does not walk. The camera is almost static with a very slight gimbal drift, keeping her the same size in the frame and the empty space above her head."
v(){ /usr/bin/python3 gen_video.py "$1" "$1.png" "$2 $C" 6s; }
v b2 "She walks slowly toward the camera across the bank hall in high heels with a confident runway stride, clearly alternating natural steps, the folder held at her side. $W" &
v b3 "She pushes the blank sheet of paper away across the table with one hand and slightly shakes her head with a sceptical look at the camera. $S" &
v b4 "She lifts the tablet slightly as if showing it and gives a small approving nod with a slight smile. $S" &
v b5 "She walks slowly toward the camera along the promenade in high heels with an elegant runway stride, clearly alternating natural steps. $W" &
wait
v b6 "She gestures with one hand back toward the billboard, then turns her face to the camera with a doubtful look and slowly shakes her head. $S" &
v b7 "She glances down at the tablet, then looks up into the lens and gives a calm approving nod. $S" &
v b8 "She tilts her head and slightly shakes it with a doubtful half-smile, arms loosely crossed. $S" &
wait
ls b?.mp4 | wc -l
