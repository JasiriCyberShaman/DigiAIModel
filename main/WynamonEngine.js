import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

let scene, camera, renderer, mixer, clock;
const actions = {};
let currentMouthAction = null;

// Glow State Variables
let glowMaterial = null;
let targetGlow = 0; 
let currentGlow = 0;

// Texture State Variables
let bodyMaterial = null;

// DETECTION: Finds the repository base path relative to where this script is hosted
const SCRIPT_URL = new URL(import.meta.url);
const pathParts = SCRIPT_URL.pathname.split('/');
pathParts.pop(); 
const REPO_BASE = SCRIPT_URL.origin + pathParts.join('/');
const DEFAULT_MODEL = `${REPO_BASE}/wanyamon.glb`;

export function initWynamon(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // --- 1. CORE ENGINE SETUP ---
    scene = new THREE.Scene();
    clock = new THREE.Clock();
    
    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(0, 0.5, 2);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    const light = new THREE.HemisphereLight(0xffffff, 0x444444, 3);
    scene.add(light);

    // --- 2. MODEL LOADING ---
    const loader = new GLTFLoader();
    loader.load(DEFAULT_MODEL, (gltf) => {
        const model = gltf.scene;
        scene.add(model);

        // MAP HARDWARE: Identify specific meshes and materials
        model.traverse((child) => {
            // Target the Horn for Glow
            if (child.isMesh && child.name === "Cone") {
                glowMaterial = child.material;
                glowMaterial.emissiveIntensity = 0;
                glowMaterial.emissive.setHex(0x00ffff); 
                console.log("System: GlowHorn mapped on 'Cone'");
            }

            // Target the Body for Texture Swaps
            if (child.isMesh && child.name === "chr321_0") {
                bodyMaterial = child.material;
                console.log("System: basemat mapped on 'chr321_0'");
            }
        });

        mixer = new THREE.AnimationMixer(model);
        gltf.animations.forEach((clip) => {
            actions[clip.name] = mixer.clipAction(clip);
        });

        if (actions['idle']) actions['idle'].play();
        
        console.log("Wynamon Engine: Online. Tracks:", Object.keys(actions));
        animate();
    });

    // --- 3. EXECUTION LOOP ---
    function animate() {
        requestAnimationFrame(animate);
        const delta = clock.getDelta();

        // LERP: Smooth transition for the horn glow
        if (glowMaterial) {
            currentGlow += (targetGlow - currentGlow) * 0.05; 
            glowMaterial.emissiveIntensity = currentGlow * 2.5; 
        }

        if (mixer) mixer.update(delta);
        renderer.render(scene, camera);
    }

    // --- 4. SIGNAL INTERRUPT HANDLER ---
    window.addEventListener("message", (e) => {
        const { type, animation, name, url, value, state, color } = e.data;

        // A. BASE ANIMATION (Exclusive)
        if (type === "SET_ANIMATION" && actions[animation]) {
            Object.values(actions).forEach(a => a.stop());
            actions[animation].play();
        }

        // B. ADDITIVE BLEND (Mouth/Roar)
        if (type === "SET_MORPH" && actions[name]) {
            if (currentMouthAction) currentMouthAction.fadeOut(0.1);
            currentMouthAction = actions[name];
            currentMouthAction.reset().setLoop(THREE.LoopOnce).fadeIn(0.1).play();
            currentMouthAction.clampWhenFinished = true;
        }

        // C. TEXTURE SWAP (Specifically targeting bodyMaterial)
        if (type === "SET_TEXTURE" && url && bodyMaterial) {
            const textureLoader = new THREE.TextureLoader();
            textureLoader.load(url, (texture) => {
                texture.flipY = false; 
                bodyMaterial.map = texture;
                bodyMaterial.needsUpdate = true;
                console.log("System: Body texture updated.");
            });
        }

        // D. MANUAL MORPH OVERRIDE
        if (type === "MANUAL_MORPH") {
            scene.traverse((child) => {
                if (child.isMesh && child.name === "chr321_0") {
                    const dict = child.morphTargetDictionary;
                    if (dict && dict["MouthOpen"] !== undefined) {
                        child.morphTargetInfluences[dict["MouthOpen"]] = value;
                    }
                }
            });
        }

        // E. GLOW CONTROL (Specifically targeting glowMaterial)
        if (type === "SET_GLOW") {
            targetGlow = state === "ON" ? 1 : 0;
            if (color && glowMaterial) {
                glowMaterial.emissive.setHex(color);
            }
        }
    });
}