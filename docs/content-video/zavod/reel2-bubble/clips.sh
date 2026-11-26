C="She does not speak, her mouth stays closed. The camera slowly tracks backward on a gimbal, keeping her framing and the empty space above her head. Photorealistic, natural smooth motion, no cuts. No text, no captions, no subtitles, no logos. Ambient sound only, no music."
v(){ /usr/bin/python3 gen_video.py "$1" "$1.png" "$2 $C" 6s; }
v b2 "She walks calmly toward the camera across the plaza between the glass towers, confident, slight smile." &
v b3 "She walks toward the camera along the bridge, glances at the skyline, then looks back into the lens with a calm nod." &
v b4 "She walks toward the camera through the lobby past the reception desk, calm and confident." &
v b5 "She walks toward the camera along the boulevard while blurred passers-by move around her, slight smile." &
wait
v b6 "She points at the dark wall screen beside her with one hand, then turns to the camera with a thoughtful look and a small nod." &
v b7 "She walks toward the camera along the construction fence while the cranes stand against the sunset sky, calm and attentive." &
v b8 "She gestures with one hand across the city lights below, then turns to the camera and nods slightly." &
wait
ls -la b?.mp4
