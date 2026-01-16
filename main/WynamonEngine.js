import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

let scene, camera, renderer, mixer, clock;
const actions = {};
let currentBaseAction = null;
let currentMouthAction = null;

// Lerp State Registers
let glowMaterial = null;
let targetGlow = 0, currentGlow = 0, glowRate = 0.05;

let bodyMaterial = null;

// Morph Target Registers
let mouthMesh = null;
let targetMouth = 0, currentMouth = 0, mouthLerpRate = 0.1;

// Animation Lerp (Crossfade)
let targetBaseRate = 0.5; // Duration of crossfade in seconds

const SCRIPT_URL = new URL(import.meta.url);
const pathParts = SCRIPT_URL.pathname.split('/');
pathParts.pop(); 
const REPO_BASE = SCRIPT_URL.origin + pathParts.join('/');
const DEFAULT_MODEL = `${REPO_BASE}/wanyamon.glb`;

export function initWynamon(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    scene = new THREE.Scene();
    clock = new THREE.Clock();
    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(0, 0.5, 2);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 3));

    const loader = new GLTFLoader();
    loader.load(DEFAULT_MODEL, (gltf) => {
        const model = gltf.scene;
        scene.add(model);

        model.traverse((child) => {
            if (child.isMesh && child.name === "Cone") {
                glowMaterial = child.material;
                glowMaterial.emissiveIntensity = 0;
            }
            if (child.isMesh && child.name === "chr321_0") {
                bodyMaterial = child.material;
                mouthMesh = child; // Reference for manual morphs
            }
        });

        mixer = new THREE.AnimationMixer(model);
        gltf.animations.forEach((clip) => {
            actions[clip.name] = mixer.clipAction(clip);
        });

        // Initialize default state
        if (actions['idle']) {
            currentBaseAction = actions['idle'];
            currentBaseAction.play();
        }
        
        animate();
    });

    function animate() {
        requestAnimationFrame(animate);
        const delta = clock.getDelta();

        // 1. LERP: Glow
        if (glowMaterial) {
            currentGlow += (targetGlow - currentGlow) * glowRate;
            glowMaterial.emissiveIntensity = currentGlow * 2.5;
        }

        // 2. LERP: Manual Morph (Mouth)
        if (mouthMesh) {
            const dict = mouthMesh.morphTargetDictionary;
            if (dict && dict["MouthOpen"] !== undefined) {
                currentMouth += (targetMouth - currentMouth) * mouthLerpRate;
                mouthMesh.morphTargetInfluences[dict["MouthOpen"]] = currentMouth;
            }
        }

        if (mixer) mixer.update(delta);
        renderer.render(scene, camera);
    }

    window.addEventListener("message", (e) => {
        const { type, animation, name, url, value, state, color, rate } = e.data;

        // A. BASE ANIMATION (Lerp via Crossfade)
        if (type === "SET_ANIMATION" && actions[animation]) {
            const nextAction = actions[animation];
            const fadeTime = rate || 0.5; // Passed from .tsx as seconds
            
            if (currentBaseAction !== nextAction) {
                nextAction.reset().fadeIn(fadeTime).play();
                if (currentBaseAction) currentBaseAction.fadeOut(fadeTime);
                currentBaseAction = nextAction;
            }
        }

        // B. ADDITIVE BLEND (Mouth/Roar)
        if (type === "SET_MORPH" && actions[name]) {
            const fade = rate || 0.1;
            if (currentMouthAction) currentMouthAction.fadeOut(fade);
            currentMouthAction = actions[name];
            currentMouthAction.reset().setLoop(THREE.LoopOnce).fadeIn(fade).play();
            currentMouthAction.clampWhenFinished = true;
        }

        // C. MANUAL MORPH (Lerp via internal drift)
        if (type === "MANUAL_MORPH") {
            targetMouth = value;
            if (rate) mouthLerpRate = rate; // "rate" is the 0.0-1.0 step size
        }

        // D. GLOW (Lerp via internal drift)
        if (type === "SET_GLOW") {
            targetGlow = state === "ON" ? 1 : 0;
            if (rate) glowRate = rate;
            if (color && glowMaterial) glowMaterial.emissive.setHex(color);
        }

        // E. TEXTURE
        if (type === "SET_TEXTURE" && url && bodyMaterial) {
            new THREE.TextureLoader().load(url, (t) => {
                t.flipY = false;
                bodyMaterial.map = t;
                bodyMaterial.needsUpdate = true;
            });
        }
    });
}