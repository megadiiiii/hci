import cv2
import insightface
from insightface.app import FaceAnalysis
import numpy as np
import os
import uuid
import time

DB = "face_db"
os.makedirs(DB, exist_ok=True)

# Load model
app = FaceAnalysis(
    name="buffalo_s",
    providers=["OpenVINOExecutionProvider", "CPUExecutionProvider"]
)
app.prepare(ctx_id=0)

# Load database
known_ids = []
known_embs = []


def load_db():
    known_ids.clear()
    known_embs.clear()

    for f in os.listdir(DB):
        if f.endswith(".npy"):
            emb = np.load(f"{DB}/{f}")
            known_embs.append(emb)
            known_ids.append(f.replace(".npy", ""))


load_db()
print("[DB] Loaded:", known_ids)

cap = cv2.VideoCapture(0)


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


print("\n=== AUTO FACE RECOGNITION STARTED ===")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    faces = app.get(frame)

    for face in faces:
        emb = face.normed_embedding

        # Compare
        best_id = None
        best_score = 0.0

        for saved_id, saved_emb in zip(known_ids, known_embs):
            score = cosine_similarity(emb, saved_emb)
            if score > best_score:
                best_score = score
                best_id = saved_id

        x1, y1, x2, y2 = face.bbox.astype(int)

        # Nếu giống người cũ
        if best_score > 0.45:
            label = f"ID {best_id}"
            color = (0, 255, 0)

        else:
            # AUTO REGISTER
            new_id = str(uuid.uuid4())[:8]
            np.save(f"{DB}/{new_id}.npy", emb)

            known_ids.append(new_id)
            known_embs.append(emb)

            label = f"NEW {new_id}"
            color = (0, 200, 255)

            print(f"[REGISTER] {new_id}")

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imshow("Auto Face System", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
