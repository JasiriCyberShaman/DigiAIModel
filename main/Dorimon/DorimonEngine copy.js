import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

/**
 * KUTI ENGINE v1.0 - The Cyber Shaman Neural Interface
 */

let scene, camera, renderer, mixer, clock;
let bodyMesh = null;
let bodyMaterial = null;
let currentBaseAction = null;
const actions = {};

// Linear Interpolation (Lerp) States
const visemeTargets = {
    "viseme_sil": 0, "viseme_PP": 0, "viseme_FF": 0, "viseme_TH": 0,
    "viseme_DD": 0, "viseme_kk": 0, "viseme_CH": 0, "viseme_SS": 0,
    "viseme_nn": 0, "viseme_RR": 0, "viseme_aa": 0, "viseme_E": 0,
    "viseme_I": 0, "viseme_O": 0, "viseme_U": 0, "viseme_AA": 0
};
const visemeCurrent = { ...visemeTargets }; 
let mouthLerpRate = 0.4; 

/**
 * 1. TEXTURE CONTROLLER
 * Swaps face textures (emotions) from any source URL.
 */
export function setKutiTexture(url) {
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
 * @param {string} containerId - The HTML div ID
 * @param {string} assetBase - The GitHub Pages URL (e.g., https://user.github.io/repo)
 */
export function initKuti(containerId, assetBase) {
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

    // MODEL LOADING FROM GITHUB
    const MODEL_PATH = `${assetBase}/models/KutiComp.glb`;
    const loader = new GLTFLoader();
    
    loader.load(MODEL_PATH, (gltf) => {
        const model = gltf.scene;
        scene.add(model);

        model.traverse((child) => {
            // Updated name check for KutiMesh
            if (child.isMesh && (child.name === "KutiMesh" || child.name === "DorimonMesh")) {
                bodyMesh = child;
                bodyMaterial = child.material;
                window.bodyMesh = child; // Debug access
            }
        });

        // ANIMATION SETUP
        mixer = new THREE.AnimationMixer(model);
        gltf.animations.forEach(clip => actions[clip.name] = mixer.clipAction(clip));
        
        // Start with Idle behavior
        if (actions['Idle.001']) actions['Idle.001'].play();
        
        animate();
    }, undefined, (error) => {
        console.error("❌ [Kuti Loader Error]:", error);
    });

    function animate() {
        requestAnimationFrame(animate);
        const delta = clock.getDelta();

        if (bodyMesh && bodyMesh.morphTargetDictionary) {
            const dict = bodyMesh.morphTargetDictionary;
            Object.keys(visemeTargets).forEach(key => {
                const idx = dict[key];
                if (idx !== undefined) {
                    visemeCurrent[key] += (visemeTargets[key] - visemeCurrent[key]) * mouthLerpRate;
                    bodyMesh.morphTargetInfluences[idx] = visemeCurrent[key];
                }
            });
        }

        if (mixer) mixer.update(delta);
        renderer.render(scene, camera);
    }

    /**
     * 3. THE MESSAGE BUS
     */
    window.addEventListener("message", (e) => {
        const { type, animation, visemes, rate } = e.data;
        if (!type) return;

        switch (type) {
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
                Object.keys(visemeTargets).forEach(k => visemeTargets[k] = 0);
                if (visemes) {
                    Object.entries(visemes).forEach(([key, weight]) => {
                        if (visemeTargets[key] !== undefined) visemeTargets[key] = weight;
                    });
                }
                if (rate) mouthLerpRate = rate;
                break;
        }
    });
}