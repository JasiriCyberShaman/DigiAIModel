import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

let scene, camera, renderer, mixer, clock;
const actions = {};
let currentMouthAction = null;

// DETECTION: Finds the repository base path relative to where this script is hosted
const SCRIPT_URL = new URL(import.meta.url);
const REPO_BASE = SCRIPT_URL.origin + SCRIPT_URL.pathname.substring(0, SCRIPT_URL.pathname.lastIndexOf('/'));
const DEFAULT_MODEL = `${REPO_BASE}/wanyamon.glb`;

/**
 * Initializes the Wynamon 3D Engine
 * @param {string} containerId - The ID of the HTML div to render in
 */
export function initWynamon(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // --- 1. CORE ENGINE SETUP ---
    scene = new THREE.Scene();
    clock = new THREE.Clock();
    
    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(0, 0.5, 2);
    camera.rotation.set(90, 0, 0);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    const light = new THREE.HemisphereLight(0xffffff, 0x444444, 3);
    scene.add(light);

    // --- 2. HARDWARE LOADING (GLB) ---
    const loader = new GLTFLoader();
    loader.load(DEFAULT_MODEL, (gltf) => {
        const model = gltf.scene;
        scene.add(model);

        // Initialize the Animation Mixer on the model
        mixer = new THREE.AnimationMixer(model);
        
        // Map all internal NLA tracks to the actions object for direct access
        gltf.animations.forEach((clip) => {
            actions[clip.name] = mixer.clipAction(clip);
        });

        // Set Default State: Idle
        if (actions['idle']) actions['idle'].play();
        
        console.log("Wynamon Engine: Hardware Synced.", Object.keys(actions));
        animate();
    });

    // --- 3. EXECUTION LOOP ---
    function animate() {
        requestAnimationFrame(animate);
        const delta = clock.getDelta();
        if (mixer) mixer.update(delta);
        renderer.render(scene, camera);
    }

    // --- 4. SIGNAL INTERRUPT HANDLER ---
    window.addEventListener("message", (e) => {
        const { type, animation, name, url } = e.data;

        // A. BASE LAYER SWITCH (Exclusive: Walk, Idle, etc.)
        if (type === "SET_ANIMATION" && actions[animation]) {
            Object.values(actions).forEach(a => a.stop());
            actions[animation].play();
            console.log(`System: Base state changed to -> ${animation}`);
        }

        // B. ADDITIVE BLEND (Parallel: Roar/MouthOpen while walking)
        if (type === "SET_MORPH" && actions[name]) {
            if (currentMouthAction) currentMouthAction.fadeOut(0.1);
            
            currentMouthAction = actions[name];
            currentMouthAction.reset()
                              .setLoop(THREE.LoopOnce)
                              .fadeIn(0.1)
                              .play();
            currentMouthAction.clampWhenFinished = true;
            console.log(`System: Blending additive track -> ${name}`);
        }

        // C. TEXTURE ENGINE (Cyber Shaman Glow Mode)
        if (type === "SET_TEXTURE" && url) {
            const textureLoader = new THREE.TextureLoader();
            textureLoader.load(url, (texture) => {
                texture.flipY = false; // Required for glTF orientation
                scene.traverse((child) => {
                    if (child.isMesh) {
                        child.material.map = texture;
                        child.material.needsUpdate = true;
                    }
                });
                console.log("System: Texture buffer swapped.");
            });
        }
    });
}