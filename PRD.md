# Product Requirements Document (PRD)
**Product Name:** Nexus Laundry AI
**Target Audience:** Commercial Dry Cleaners, Industrial Laundry Facilities, Textile Recyclers.

## 1. Product Vision
To fully automate the garment intake and sorting process, reducing human error to 0%, preventing batch contamination, and lowering operational labor costs through an intelligent robotic pipeline.

## 2. Key Features
### 2.1 Multi-Modal AI Sorting
- The system must identify the primary color of the garment.
- The system must identify the fabric texture (e.g., Cotton, Silk, Denim).
- The system must localize and classify specific visible stains (e.g., Oil, Blood, Wine).

### 2.2 Advanced Hardware Synergy
- The system must integrate with Electronic Noses (E-Noses) to flag foul odors or hazardous chemicals invisible to cameras.
- The system must integrate with UV light sensors to flag biological or chemical stains that are visually hidden.

### 2.3 Factory Operator Dashboard
- A high-end, premium user interface accessible on factory floor touchscreens.
- Must display real-time live-feeds with bounding box overlays.
- Must display system health, confidence metrics, and the final routing decision.

## 3. User Flows
1. **Garment Intake:** Garment is placed on the scanning conveyor.
2. **Analysis:** Garment passes under RGB camera, UV camera, and E-Nose.
3. **Inference:** The AI pipeline analyzes the data concurrently.
4. **Decision:** The Decision Engine calculates the optimal washing bin (e.g., "Bin D - Biohazard/Heavy Wash").
5. **Execution:** The robotic arm picks up the garment and places it in the designated bin.
6. **Telemetry:** The operator dashboard updates with the garment's metadata and routing history.

## 4. Success Metrics
- **Sorting Accuracy:** > 99.5% accuracy on color and fabric type.
- **Throughput:** Process and sort 1 garment per second.
- **Uptime:** 99.9% availability during shift hours.
