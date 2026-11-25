C="She does not speak, her mouth stays closed. The camera slowly tracks backward on a gimbal, keeping her framing and the empty space above her head. Photorealistic, natural smooth motion, no cuts. No text, no captions, no subtitles, no logos. Ambient sound only, no music."
v(){ /usr/bin/python3 gen_video.py "$1" "$1.png" "$2 $C" 6s; }
v b2 "She walks calmly toward the camera through the bank hall holding the folder of documents, confident, slight smile." &
v b3 "She pushes the blank sheet of paper away across the table and slightly shakes her head with a sceptical look at the camera." &
v b4 "She walks toward the camera and raises the tablet to chest height as if showing it, a slight approving nod." &
v b5 "She walks toward the camera along the promenade between the lit towers, confident, a slight approving nod." &
wait
v b6 "She gestures back at the billboard, then turns to the camera with a doubtful look and slowly shakes her head." &
v b7 "She walks toward the camera, glances down at the tablet, then looks up into the lens and nods." &
v b8 "She walks toward the camera away from the scale model, slightly shakes her head with a doubtful half-smile." &
wait
ls -la b?.mp4
