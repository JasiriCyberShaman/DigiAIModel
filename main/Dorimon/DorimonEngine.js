import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

let scene, camera, renderer, mixer, clock, controls;
const actions = {};
let currentBaseAction = null;

// Hardware References
let bodyMesh = null;
let bodyMaterial = null;

// 1. DEDICATED VISEME BUS (Lip Sync)
const visemeTargets = { "A": 0, "E": 0, "I": 0, "O": 0, "U": 0, "BASE": 0 };
const visemeCurrent = { "A": 0, "E": 0, "I": 0, "O": 0, "U": 0, "BASE": 0 };
let mouthLerpRate = 0.15;

// 2. GENERIC MORPH BUS (GPIO for Expressions)
const genericMorphTargets = {}; // Stores { "TargetName": targetValue }
const genericMorphCurrent = {}; // Stores { "TargetName": currentValue }
let genericLerpRate = 0.1;

const SCRIPT_URL = new URL(import.meta.url);
const pathParts = SCRIPT_URL.pathname.split('/');
pathParts.pop(); 
const REPO_BASE = SCRIPT_URL.origin + pathParts.join('/');
const DEFAULT_MODEL = `${REPO_BASE}/DorimonComp.glb`;

export function initDorimon(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // --- ENGINE CORE ---
    scene = new THREE.Scene();
    clock = new THREE.Clock();
    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(0, 0, .5);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // --- INTERACTION CONTROLS ---
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.target.set(0, 0.01, 0);

    // BRIGHTNESS FIX: Proper Color Management & Exposure
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.5; // Boosts global brightness

    scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 3));

    // --- 3. MODEL LOADING ---
    const loader = new GLTFLoader();
    loader.load(DEFAULT_MODEL, (gltf) => {
        const model = gltf.scene;
        scene.add(model);

        model.traverse((child) => {
            if (child.isMesh && child.name === "DorimonMesh") {
                bodyMaterial = child.material;
                bodyMesh = child;

                // FORCE INITIAL TEXTURE: Ensures he isn't black on boot
                const texLoader = new THREE.TextureLoader();
                const defaultTexUrl = `${REPO_BASE}/Neutral466.jpg`; // Ensure this path is correct
                
                texLoader.load(defaultTexUrl, (t) => {
                    t.colorSpace = THREE.SRGBColorSpace;
                    t.flipY = false;
                    bodyMaterial.map = t;
                    bodyMaterial.needsUpdate = true;
                    console.log("[Dorimon OS]: Default texture successfully mapped.");
                });
            }
        });

        mixer = new THREE.AnimationMixer(model);
        gltf.animations.forEach((clip) => {
            actions[clip.name] = mixer.clipAction(clip);
        });

        if (actions['Idle.001']) actions['Idle.001'].play();
        animate();
    });

    function animate() {
        requestAnimationFrame(animate);
        const delta = clock.getDelta();

        if (bodyMesh) {
            const dict = bodyMesh.morphTargetDictionary;
            if (dict) {
                // Process Dedicated Visemes
                Object.keys(visemeTargets).forEach(key => {
                    if (dict[key] !== undefined) {
                        visemeCurrent[key] += (visemeTargets[key] - visemeCurrent[key]) * mouthLerpRate;
                        bodyMesh.morphTargetInfluences[dict[key]] = visemeCurrent[key];
                    }
                });

                // Process Generic Morph Targets (expressions, twitches, etc.)
                Object.keys(genericMorphTargets).forEach(name => {
                    if (dict[name] !== undefined) {
                        // Initialize current tracker if it doesn't exist
                        if (genericMorphCurrent[name] === undefined) genericMorphCurrent[name] = 0;
                        
                        // Lerp towards target
                        genericMorphCurrent[name] += (genericMorphTargets[name] - genericMorphCurrent[name]) * genericLerpRate;
                        bodyMesh.morphTargetInfluences[dict[name]] = genericMorphCurrent[name];
                    }
                });
            }
        }

        if (controls) controls.update();
        if (mixer) mixer.update(delta);
        renderer.render(scene, camera);
    }

    // --- SIGNAL HANDLER ---
    window.addEventListener("message", (e) => {
        const { type, animation, visemes, morphName, value, rate, url } = e.data;

        if (type === "RESET_CAMERA") {
            camera.position.set(0, 0.5, 2);
            controls.target.set(0, 0.5, 0);
            controls.update();
        }

        // Dedicated Lip Sync Signal
        if (type === "SET_VISEMES") {
            if (rate) mouthLerpRate = rate;
            Object.assign(visemeTargets, visemes);
        }

        // Generic Expression Signal (GPIO)
        if (type === "SET_GENERIC_MORPH" && morphName) {
            genericMorphTargets[morphName] = value;
            if (rate) genericLerpRate = rate;
            console.log(`[Dorimon OS]: Morph target '${morphName}' set to ${value}`);
        }

        if (type === "SET_ANIMATION" && actions[animation]) {
            const next = actions[animation];
            const fade = rate || 0.5;
            if (currentBaseAction !== next) {
                next.reset().fadeIn(fade).play();
                if (currentBaseAction) currentBaseAction.fadeOut(fade);
                currentBaseAction = next;
            }
        }

        if (type === "SET_TEXTURE" && url && bodyMaterial) {
            new THREE.TextureLoader().load(url, (t) => {
                t.colorSpace = THREE.SRGBColorSpace;
                t.flipY = false;
                bodyMaterial.map = t;
                bodyMaterial.needsUpdate = true;
            });
        }
    });
}
