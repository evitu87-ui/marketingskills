V=../avatar/refs; H=/home/user/marketingskills/docs/content-video/assets/hosts
LB="Fashion lookbook photograph for a personal brand. Plain warm light-grey seamless studio backdrop, soft diffused daylight, full-frame camera, 50mm lens, photorealistic, natural skin texture, not an illustration. Vertical 9:16 frame. Full figure from head to shoes, standing, centred, relaxed confident pose, small margins above the head and below the shoes. No text, no logos, no watermark. One person."
VIT="The man from the reference photos: keep his identity exactly, same shaved bald head, same face shape, dark eyebrows and dark eyes, short dark stubble, same age (early forties) and solid athletic build."
E="The woman from the reference photos: keep her identity exactly, same face, same long sleek dark brown hair, same slim figure."
G="The woman from the reference photos: keep her identity exactly, same face, same long light honey-blonde hair, same slim figure."
g(){ /usr/bin/python3 gen.py "$@"; }
g v1 "$LB $VIT Outfit: dark navy chalk-stripe three-piece suit, crisp white shirt, dark navy silk tie, black oxford shoes, hands relaxed, calm direct look into the camera." $V/office_solo.jpg $V/office_pair.jpg &
g v2 "$LB $VIT Outfit: dark navy blazer, white open-collar shirt without a tie, light grey tailored trousers, brown leather loafers, a steel wristwatch, one hand in the trouser pocket, slight smile." $V/office_solo.jpg $V/office_pair.jpg &
g v3 "$LB $VIT He wears the same black thick-rimmed acetate glasses as in the close-up reference photo with glasses. Outfit: black fine-knit turtleneck under a charcoal-grey unstructured blazer, dark charcoal trousers, black leather chelsea boots, calm thoughtful look into the camera." $V/office_solo.jpg $V/office_pair.jpg vit_glasses_crop.jpg &
g v4 "$LB $VIT Outfit: sand-beige linen blazer, white polo shirt, off-white chinos, tan suede loafers, a steel wristwatch, relaxed open posture, light smile." $V/office_solo.jpg $V/office_pair.jpg &
wait
g e2 "$LB $E Hair in a sleek low ponytail. Outfit: black tailored trouser suit, single-button blazer worn closed with a thin gold belt at the waist, wide-leg trousers, black pointed stiletto pumps, small gold hoop earrings, elegant graceful posture." $H/host_E_face.jpg $H/host_E_look2_three.jpg $H/host_E_look2_full.jpg &
g e3 "$LB $E Hair loose and straight. She wears thin gold-rimmed round glasses. Outfit: emerald-green silk blouse tucked into high-waisted cream wide-leg trousers, nude stiletto heels, delicate gold necklace, elegant graceful posture." $H/host_E_face.jpg $H/host_E_look2_three.jpg $H/host_E_look2_full.jpg &
g e4 "$LB $E Hair loose with a soft wave at the ends. Outfit: deep navy fitted midi sheath dress with three-quarter sleeves and a thin tan belt, beige stiletto heels, gold bracelet, elegant graceful posture." $H/host_E_face.jpg $H/host_E_look2_three.jpg $H/host_E_look2_full.jpg &
g g2 "$LB $G Hair straight and loose. Outfit: white tailored trouser suit with a relaxed blazer over an ivory silk camisole, nude pointed stiletto heels, thin gold chain, elegant graceful posture." $H/host_G_face.jpg $H/host_G_look2_three.jpg $H/host_G_look2_full.jpg &
wait
g g3 "$LB $G Hair in soft waves. Outfit: terracotta wrap midi dress with long sleeves, gold strappy high-heeled sandals, small gold earrings, elegant graceful posture." $H/host_G_face.jpg $H/host_G_look2_three.jpg $H/host_G_look2_full.jpg &
g g4 "$LB $G Hair in a low bun with loose strands. She wears tortoiseshell acetate glasses. Outfit: light-blue oversized cotton poplin shirt half-tucked into white tailored trousers, tan leather belt, tan pointed heels, elegant graceful posture." $H/host_G_face.jpg $H/host_G_look2_three.jpg $H/host_G_look2_full.jpg &
wait
