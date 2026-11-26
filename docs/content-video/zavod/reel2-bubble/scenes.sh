g(){ /usr/bin/python3 gen_still.py "$1" "$2"; }
g b1 "Scene: Dubai Marina waterfront promenade at sunset, yachts and towers softly blurred low in the background, warm glowing sky fills the upper part of the frame. Three-quarter-length shot from mid-thigh up: she stands facing the camera, looking straight into the lens, lips slightly parted as if about to speak, confident calm expression." &
g b2 "Scene: a modern business district in the morning, glass office towers at the sides, clear pale morning sky fills the upper part of the frame. Full-body shot head to toe: she walks toward the camera along a wide plaza, looking into the lens." &
g b3 "Scene: a pedestrian bridge over a city canal in daytime, skyline low in the distance, open blue sky fills the upper part of the frame. Full-body shot head to toe: she walks toward the camera along the bridge, glancing at the city and back to the lens." &
wait
g b4 "Scene: a premium residential lobby with a very high dark ceiling and a stone reception desk low in the background, the upper part of the frame is a plain dark ceiling. Full-body shot head to toe: she walks toward the camera past the reception desk, looking into the lens." &
g b5 "Scene: a lively pedestrian boulevard in the evening, blurred passers-by and warm shop lights low in the frame, deep blue dusk sky fills the upper part of the frame. Full-body shot head to toe: she walks toward the camera among the people, looking into the lens." &
g b6 "Scene: an office with a panoramic window in the evening, city lights outside, a plain dark ceiling fills the upper part of the frame. Three-quarter-length shot from mid-thigh up: she stands beside a large blank dark wall screen and points at it with one hand, looking into the lens." &
wait
g b7 "Scene: a construction site with tower cranes at sunset behind a low hoarding fence, orange and pink sky fills the upper part of the frame. Full-body shot head to toe: she walks toward the camera along the fence, looking into the lens." &
g b8 "Scene: an open observation deck at night above the city, a carpet of city lights low in the frame, dark night sky fills the upper part of the frame. Three-quarter-length shot from mid-thigh up: she gestures with one hand toward the city lights below, looking into the lens." &
g b9 "Scene: an evening lounge with a plain dark wall behind her filling the upper part of the frame, a floor lamp glowing at the side. Medium shot: she sits in a designer armchair facing the camera, her head at about half of the frame height, hands relaxed, looking straight into the lens, lips slightly parted as if about to speak, warm friendly expression." &
wait
ls -la b?.png | awk '{print $5,$9}'
