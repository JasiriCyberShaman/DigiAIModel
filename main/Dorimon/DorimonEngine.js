import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

/**
 * CONFIGURATION & HARDWARE CONSTANTS
 */
const LOCAL_IP = "192.168.0.31";
const MODEL_PATH = `https://${LOCAL_IP}:8000/Dorimon/DorimonComp.glb`;

let scene, camera, renderer, mixer, clock;
let bodyMesh = null;
let bodyMaterial = null;
let currentBaseAction = null;
const actions = {};

// Linear Interpolation (Lerp) States: Stores where the mouth IS vs where it's GOING
const visemeTargets = {
    "viseme_sil": 0, "viseme_PP": 0, "viseme_FF": 0, "viseme_TH": 0,
    "viseme_DD": 0, "viseme_kk": 0, "viseme_CH": 0, "viseme_SS": 0,
    "viseme_nn": 0, "viseme_RR": 0, "viseme_aa": 0, "viseme_E": 0,
    "viseme_I": 0, "viseme_O": 0, "viseme_U": 0, "viseme_AA": 0
};
const visemeCurrent = { ...visemeTargets }; // Current smoothed values
let mouthLerpRate = 0.4; // Smoothing factor (0.1 = slow/mushy, 0.8 = fast/snappy)

/**
 * 1. TEXTURE CONTROLLER
 * Swaps the face texture for different moods/emotions.
 */
export function setTexture(url) {
    if (!bodyMaterial) return;
    const loader = new THREE.TextureLoader();
    loader.setCrossOrigin('anonymous'); 
    loader.load(url, (t) => {
        t.colorSpace = THREE.SRGBColorSpace;
        t.flipY = false;
        bodyMaterial.map = t;
        bodyMaterial.needsUpdate = true;
    });
}

/**
 * 2. INITIALIZATION ENGINE
 * Sets up the 3D world and loads the Digital Lifeform.
 */
export function initDorimon(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // SCENE SETUP
    scene = new THREE.Scene();
    clock = new THREE.Clock();
    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.01, 100);
    camera.position.set(0, 0.1, 0.5);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.appendChild(renderer.domElement);

    // LIGHTING (The Cyber Shaman Glow)
    scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 2.5));
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
    dirLight.position.set(1, 2, 3);
    scene.add(dirLight);

    // MODEL LOADING
    const loader = new GLTFLoader();
    loader.load(MODEL_PATH, (gltf) => {
        const model = gltf.scene;
        scene.add(model);

        model.traverse((child) => {
            if (child.isMesh && child.name === "DorimonMesh") {
                bodyMesh = child;
                bodyMaterial = child.material;
                // Expose to window for live console debugging if needed
                window.bodyMesh = child;
            }
        });

        // ANIMATION SETUP
        mixer = new THREE.AnimationMixer(model);
        gltf.animations.forEach(clip => actions[clip.name] = mixer.clipAction(clip));
        
        // Start with Idle behavior
        if (actions['Idle.001']) actions['Idle.001'].play();
        
        animate();
    });

    /**
     * 3. THE FRAME LOOP (60fps)
     * This handles the math for smooth movement every single frame.
     */
    function animate() {
        requestAnimationFrame(animate);
        const delta = clock.getDelta();

        if (bodyMesh && bodyMesh.morphTargetDictionary) {
            const dict = bodyMesh.morphTargetDictionary;
            
            // SMOTHED VISEME INTERPOLATION
            // This prevents "shaking" and makes the mouth flow between shapes.
            Object.keys(visemeTargets).forEach(key => {
                const idx = dict[key];
                if (idx !== undefined) {
                    // Classic Lerp formula: Current += (Target - Current) * Factor
                    visemeCurrent[key] += (visemeTargets[key] - visemeCurrent[key]) * mouthLerpRate;
                    bodyMesh.morphTargetInfluences[idx] = visemeCurrent[key];
                }
            });
        }

        if (mixer) mixer.update(delta);
        renderer.render(scene, camera);
    }

    /**
     * 4. THE MESSAGE BUS (The Nervous System)
     * Listens for signals from the Framer Overrides / Python Hub.
     */
    window.addEventListener("message", (e) => {
        const { type, animation, visemes, rate, url } = e.data;
        if (!type) return;

        if (type === "RESET_CAMERA") {
            camera.position.set(0, 1, 2);
            controls.target.set(0, 0.1, 0);
            controls.update();
        }

            case "SET_ANIMATION":
                if (actions[animation]) {
                    const next = actions[animation];
                    const fade = rate || 0.5;
                    if (currentBaseAction !== next) {
                        next.reset().fadeIn(fade).play();
                        if (currentBaseAction) currentBaseAction.fadeOut(fade);
                        currentBaseAction = next;
                    }
                }
                break;

            case "SET_VISEMES":
                // Reset all targets to 0 (Silence) before applying new weights
                Object.keys(visemeTargets).forEach(k => visemeTargets[k] = 0);
                
                // Apply new viseme weights from the Wawa sensor
                if (visemes) {
                    Object.entries(visemes).forEach(([key, weight]) => {
                        if (visemeTargets[key] !== undefined) {
                            visemeTargets[key] = weight;
                        }
                    });
                }
                if (rate) mouthLerpRate = rate;
                break;
        }
    });
}