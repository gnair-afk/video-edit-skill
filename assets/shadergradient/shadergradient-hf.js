// ShaderGradient for HyperFrames: a plain-JS, seek-safe port of ruucm/shadergradient (MIT, see LICENSE).
//
// The React version runs on a wall clock. Here every frame is a pure function of HyperFrames time:
// the shader noise reads uTime = startTime + t, the halftone "grain" is stateless, and nothing uses
// requestAnimationFrame, so the same t always renders the same picture.
//
// Usage (composition needs an importmap for "three" and "three/addons/", pinned to the same version):
//   import { mountShaderGradient } from './assets/shadergradient/shadergradient-hf.js'
//   mountShaderGradient(document.getElementById('sg'), { preset: 'halo', color1: '#D2583C', loop: 5 })
// Options: any ShaderGradient prop (type, color1-3, uSpeed, uStrength, uDensity, uFrequency, uAmplitude,
// positionX/Y/Z, rotationX/Y/Z, cAzimuthAngle, cPolarAngle, cDistance, cameraZoom, brightness, reflection,
// grain 'on'|'off', fov), or urlString (copied from shadergradient.co/customize), plus:
//   width, height   canvas size in px (default 1080 x 1920)
//   startTime       noise time at t = 0 (default: the preset's uTime)
//   loop            seconds; makes the motion loop seamlessly over that length (default off)
// lightType 'env' (HDR reflections) is not ported: it falls back to the '3d' ambient light.
import * as THREE from 'three'
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js'
import { HalftonePass } from 'three/addons/postprocessing/HalftonePass.js'

// The ten presets from shadergradient's presets.ts (only the props that change the picture).
export const PRESETS = {
  halo: { type: 'plane', uAmplitude: 1, uDensity: 1.3, uSpeed: 0.4, uStrength: 4, uTime: 0, uFrequency: 5.5, brightness: 1.2, cAzimuthAngle: 180, cDistance: 3.6, cPolarAngle: 90, cameraZoom: 1, color1: '#ff5005', color2: '#dbba95', color3: '#d0bce1', grain: 'on', positionX: -1.4, positionY: 0, positionZ: 0, reflection: 0.1, rotationX: 0, rotationY: 10, rotationZ: 50 },
  pensive: { type: 'sphere', uAmplitude: 7, uDensity: 0.8, uFrequency: 5.5, uSpeed: 0.3, uStrength: 0.4, uTime: 0, brightness: 1.5, cAzimuthAngle: 250, cDistance: 1.5, cPolarAngle: 140, cameraZoom: 12.5, color1: '#809bd6', color2: '#910aff', color3: '#af38ff', grain: 'on', positionX: 0, positionY: 0, positionZ: 0, reflection: 0.5, rotationX: 0, rotationY: 0, rotationZ: 140 },
  mint: { type: 'waterPlane', uAmplitude: 0, uDensity: 1.2, uFrequency: 0, uSpeed: 0.2, uStrength: 3.4, uTime: 0, brightness: 1.2, cAzimuthAngle: 170, cDistance: 4.4, cPolarAngle: 70, cameraZoom: 1, color1: '#94ffd1', color2: '#6bf5ff', color3: '#ffffff', grain: 'off', positionX: 0, positionY: 0.9, positionZ: -0.3, reflection: 0.1, rotationX: 45, rotationY: 0, rotationZ: 0 },
  interstella: { type: 'sphere', uAmplitude: 3.2, uDensity: 0.8, uFrequency: 5.5, uSpeed: 0.3, uStrength: 0.3, uTime: 0, brightness: 0.8, cAzimuthAngle: 270, cDistance: 0.5, cPolarAngle: 180, cameraZoom: 15.1, color1: '#73bfc4', color2: '#ff810a', color3: '#8da0ce', grain: 'on', positionX: -0.1, positionY: 0, positionZ: 0, reflection: 0.4, rotationX: 0, rotationY: 130, rotationZ: 70 },
  nightyNight: { type: 'waterPlane', uAmplitude: 0, uDensity: 1.5, uFrequency: 0, uSpeed: 0.3, uStrength: 1.5, uTime: 8, brightness: 1, cAzimuthAngle: 180, cDistance: 2.8, cPolarAngle: 80, cameraZoom: 9.1, color1: '#606080', color2: '#8d7dca', color3: '#212121', grain: 'on', positionX: 0, positionY: 0, positionZ: 0, reflection: 0.1, rotationX: 50, rotationY: 0, rotationZ: -60 },
  violaOrientalis: { type: 'sphere', uAmplitude: 1.4, uDensity: 1.1, uSpeed: 0.1, uStrength: 1, uTime: 0, uFrequency: 5.5, brightness: 1.1, cAzimuthAngle: 0, cDistance: 7.1, cPolarAngle: 140, cameraZoom: 17.3, color1: '#ffffff', color2: '#ffbb00', color3: '#0700ff', grain: 'off', positionX: 0, positionY: 0, positionZ: 0, reflection: 0.1, rotationX: 0, rotationY: 0, rotationZ: 0 },
  universe: { type: 'waterPlane', uAmplitude: 0, uDensity: 1.1, uSpeed: 0.1, uStrength: 2.4, uTime: 0.2, uFrequency: 5.5, brightness: 1.1, cAzimuthAngle: 180, cDistance: 3.9, cPolarAngle: 115, cameraZoom: 1, color1: '#5606ff', color2: '#fe8989', color3: '#000000', grain: 'off', positionX: -0.5, positionY: 0.1, positionZ: 0, reflection: 0.1, rotationX: 0, rotationY: 0, rotationZ: 235 },
  sunset: { type: 'sphere', uAmplitude: 1.4, uDensity: 1.1, uSpeed: 0.1, uStrength: 0.4, uTime: 0, uFrequency: 5.5, brightness: 1.5, cAzimuthAngle: 60, cDistance: 7.1, cPolarAngle: 90, cameraZoom: 15.3, color1: '#ff7a33', color2: '#33a0ff', color3: '#ffc53d', grain: 'off', positionX: 0, positionY: -0.15, positionZ: 0, reflection: 0.1, rotationX: 0, rotationY: 0, rotationZ: 0 },
  mandarin: { type: 'waterPlane', uAmplitude: 0, uDensity: 1.8, uSpeed: 0.2, uStrength: 3, uTime: 0.2, uFrequency: 5.5, brightness: 1.2, cAzimuthAngle: 180, cDistance: 2.4, cPolarAngle: 95, cameraZoom: 1, color1: '#ff6a1a', color2: '#c73c00', color3: '#FD4912', grain: 'off', positionX: 0, positionY: -2.1, positionZ: 0, reflection: 0.1, rotationX: 0, rotationY: 0, rotationZ: 225 },
  cottonCandy: { type: 'waterPlane', uAmplitude: 0, uDensity: 1, uSpeed: 0.3, uStrength: 3, uTime: 0.2, uFrequency: 5.5, brightness: 1.2, cAzimuthAngle: 180, cDistance: 2.9, cPolarAngle: 120, cameraZoom: 1, color1: '#ebedff', color2: '#f3f2f8', color3: '#dbf8ff', grain: 'off', positionX: 0, positionY: 1.8, positionZ: 0, reflection: 0.1, rotationX: 0, rotationY: 0, rotationZ: -90 },
}

// Same as the original's planeGeometry / icosahedronGeometry sizes (meshCount 192).
const MESH_COUNT = 192
const SPHERE_DISTANCE = 14

// Parses a shadergradient.co/customize URL (or just its ?query) into props.
export function parseUrlString(urlString) {
  const q = urlString.includes('?') ? urlString.slice(urlString.indexOf('?') + 1) : urlString
  const out = {}
  for (const [k, raw] of new URLSearchParams(q)) {
    if (raw === 'true' || raw === 'false') out[k] = raw === 'true'
    else if (raw !== '' && !isNaN(Number(raw))) out[k] = Number(raw)
    else out[k] = raw
  }
  return out
}

// GLSL noise from shadergradient (hughsk/glsl-noise): classic for planes, periodic for the sphere.
const NOISE = /* glsl */ `
vec3 sg_mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 sg_mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 sg_permute(vec4 x) { return sg_mod289(((x * 34.0) + 1.0) * x); }
vec4 sg_taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
vec3 sg_fade(vec3 t) { return t * t * t * (t * (t * 6.0 - 15.0) + 10.0); }
float sg_noise(vec3 P, vec3 rep, bool periodic) {
  vec3 Pi0 = periodic ? mod(floor(P), rep) : floor(P);
  vec3 Pi1 = periodic ? mod(Pi0 + vec3(1.0), rep) : Pi0 + vec3(1.0);
  Pi0 = sg_mod289(Pi0);
  Pi1 = sg_mod289(Pi1);
  vec3 Pf0 = fract(P);
  vec3 Pf1 = Pf0 - vec3(1.0);
  vec4 ix = vec4(Pi0.x, Pi1.x, Pi0.x, Pi1.x);
  vec4 iy = vec4(Pi0.yy, Pi1.yy);
  vec4 iz0 = Pi0.zzzz;
  vec4 iz1 = Pi1.zzzz;
  vec4 ixy = sg_permute(sg_permute(ix) + iy);
  vec4 ixy0 = sg_permute(ixy + iz0);
  vec4 ixy1 = sg_permute(ixy + iz1);
  vec4 gx0 = ixy0 * (1.0 / 7.0);
  vec4 gy0 = fract(floor(gx0) * (1.0 / 7.0)) - 0.5;
  gx0 = fract(gx0);
  vec4 gz0 = vec4(0.5) - abs(gx0) - abs(gy0);
  vec4 sz0 = step(gz0, vec4(0.0));
  gx0 -= sz0 * (step(0.0, gx0) - 0.5);
  gy0 -= sz0 * (step(0.0, gy0) - 0.5);
  vec4 gx1 = ixy1 * (1.0 / 7.0);
  vec4 gy1 = fract(floor(gx1) * (1.0 / 7.0)) - 0.5;
  gx1 = fract(gx1);
  vec4 gz1 = vec4(0.5) - abs(gx1) - abs(gy1);
  vec4 sz1 = step(gz1, vec4(0.0));
  gx1 -= sz1 * (step(0.0, gx1) - 0.5);
  gy1 -= sz1 * (step(0.0, gy1) - 0.5);
  vec3 g000 = vec3(gx0.x, gy0.x, gz0.x);
  vec3 g100 = vec3(gx0.y, gy0.y, gz0.y);
  vec3 g010 = vec3(gx0.z, gy0.z, gz0.z);
  vec3 g110 = vec3(gx0.w, gy0.w, gz0.w);
  vec3 g001 = vec3(gx1.x, gy1.x, gz1.x);
  vec3 g101 = vec3(gx1.y, gy1.y, gz1.y);
  vec3 g011 = vec3(gx1.z, gy1.z, gz1.z);
  vec3 g111 = vec3(gx1.w, gy1.w, gz1.w);
  vec4 norm0 = sg_taylorInvSqrt(vec4(dot(g000, g000), dot(g010, g010), dot(g100, g100), dot(g110, g110)));
  g000 *= norm0.x; g010 *= norm0.y; g100 *= norm0.z; g110 *= norm0.w;
  vec4 norm1 = sg_taylorInvSqrt(vec4(dot(g001, g001), dot(g011, g011), dot(g101, g101), dot(g111, g111)));
  g001 *= norm1.x; g011 *= norm1.y; g101 *= norm1.z; g111 *= norm1.w;
  float n000 = dot(g000, Pf0);
  float n100 = dot(g100, vec3(Pf1.x, Pf0.yz));
  float n010 = dot(g010, vec3(Pf0.x, Pf1.y, Pf0.z));
  float n110 = dot(g110, vec3(Pf1.xy, Pf0.z));
  float n001 = dot(g001, vec3(Pf0.xy, Pf1.z));
  float n101 = dot(g101, vec3(Pf1.x, Pf0.y, Pf1.z));
  float n011 = dot(g011, vec3(Pf0.x, Pf1.yz));
  float n111 = dot(g111, Pf1);
  vec3 fade_xyz = sg_fade(Pf0);
  vec4 n_z = mix(vec4(n000, n100, n010, n110), vec4(n001, n101, n011, n111), fade_xyz.z);
  vec2 n_yz = mix(n_z.xy, n_z.zw, fade_xyz.y);
  return 2.2 * mix(n_yz.x, n_yz.y, fade_xyz.x);
}
`

// Vertex displacement, one per mesh type, following shaders/defaults/<type>/vertex.glsl.
// Loop mode samples noise on a circle (4 points, cosine weights), exactly like the original.
const VERTEX_HEAD = /* glsl */ `
uniform float uTime;
uniform float uSpeed;
uniform float uLoop;
uniform float uLoopDuration;
uniform float uNoiseDensity;
uniform float uNoiseStrength;
uniform float uFrequency;
uniform float uAmplitude;
varying vec3 vSgPos;
${NOISE}
vec3 sg_rotateY(vec3 v, float a) {
  float s = sin(a); float c = cos(a);
  return mat3(c, 0.0, -s, 0.0, 1.0, 0.0, s, 0.0, c) * v;
}
float sg_sample(vec3 p, bool sphere) {
  return sphere ? sg_noise(p, vec3(10.0), true) : sg_noise(p, vec3(0.0), false);
}
`

function vertexBody(type) {
  const sphere = type === 'sphere'
  return /* glsl */ `
  float sgT = uTime * uSpeed;
  float sgDist;
  float sgAngle = 0.0;
  vec3 sgBase = ${sphere ? 'normal' : '0.43 * position * uNoiseDensity'};
  if (uLoop > 0.5) {
    float la = uTime / uLoopDuration * 6.28318530718;
    float r = 5.0 * uSpeed;
    float n = 0.0; float wsum = 0.0; float ax = 0.0;
    for (int i = 0; i < 4; i++) {
      float a = la + float(i) * 1.57079632679;
      vec3 off = vec3(cos(a) * r, sin(a) * r, 0.0);
      float w = (cos(a) + 1.0) * 0.5;
      n += w * sg_sample(${sphere ? '(sgBase + off) * uNoiseDensity' : 'sgBase + off'}, ${sphere});
      ax += w * off.x;
      wsum += w;
    }
    n /= wsum; ax /= wsum;
    ${sphere ? 'sgDist = n * 1.5 * uNoiseStrength; sgAngle = sin(uv.y * uFrequency + ax) * uAmplitude;' : 'sgDist = 0.75 * n * 1.5;'}
  } else {
    ${sphere
      ? 'sgDist = sg_sample((sgBase + sgT) * uNoiseDensity, true) * uNoiseStrength; sgAngle = sin(uv.y * uFrequency + sgT) * uAmplitude;'
      : 'sgDist = 0.75 * sg_sample(sgBase + sgT, false);'}
  }
  vec3 sgPos = position + normal * sgDist${sphere ? '' : ' * uNoiseStrength'};
  ${sphere ? 'sgPos = sg_rotateY(sgPos, sgAngle);' : ''}
  vSgPos = sgPos;
  transformed = sgPos;
`
}

// Base colour, following shaders/defaults/<type>/fragment.glsl. Lighting then runs as normal.
function colorBody(type) {
  if (type === 'sphere') {
    return 'diffuseColor.rgb = mix(uC3, mix(uC2, uC1, smoothstep(-1.0, 1.0, vSgPos.y)), distance(vSgPos, vec3(0.0)));'
  }
  return 'diffuseColor.rgb = mix(mix(uC1, uC2, smoothstep(-3.0, 3.0, vSgPos.x)), uC3, vSgPos.z);'
}

// Original passes hex/255 straight into the shader (no sRGB decode) and renders with linear output and
// no tone mapping, so the colours here are raw 0-1 values on purpose.
function hexToVec3(hex) {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  if (!m) throw new Error('shadergradient: colours must be #rrggbb, got ' + hex)
  return new THREE.Vector3(parseInt(m[1], 16) / 255, parseInt(m[2], 16) / 255, parseInt(m[3], 16) / 255)
}

const d2r = (d) => (d / 180) * Math.PI

export function mountShaderGradient(canvas, options = {}) {
  const fromUrl = options.urlString ? parseUrlString(options.urlString) : {}
  const base = PRESETS[options.preset || fromUrl.preset || 'halo'] || PRESETS.halo
  const p = { fov: 45, ...base, ...fromUrl, ...options }
  const width = p.width || 1080
  const height = p.height || 1920
  const startTime = p.startTime ?? p.uTime ?? 0

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true })
  renderer.setPixelRatio(1)
  renderer.setSize(width, height, false)
  renderer.outputColorSpace = THREE.LinearSRGBColorSpace
  renderer.toneMapping = THREE.NoToneMapping

  const scene = new THREE.Scene()
  // lightType '3d': ambient at brightness * PI (as in Lights.tsx). 'env' is not ported.
  scene.add(new THREE.AmbientLight(0xffffff, (p.brightness || 1) * Math.PI))

  const camera = new THREE.PerspectiveCamera(p.fov, width / height, 0.1, 1000)
  // camera-controls: orbit around the origin, Y up. Spheres orbit at 14 and zoom; planes dolly.
  const dist = p.type === 'sphere' ? SPHERE_DISTANCE : p.cDistance
  const polar = Math.min(Math.max(d2r(p.cPolarAngle), 1e-5), Math.PI - 1e-5)
  const az = d2r(p.cAzimuthAngle)
  camera.position.set(dist * Math.sin(polar) * Math.sin(az), dist * Math.cos(polar), dist * Math.sin(polar) * Math.cos(az))
  camera.lookAt(0, 0, 0)
  camera.zoom = p.type === 'sphere' ? p.cameraZoom || 1 : 1
  camera.updateProjectionMatrix()

  const geometry =
    p.type === 'sphere'
      ? new THREE.IcosahedronGeometry(1, MESH_COUNT / 3)
      : new THREE.PlaneGeometry(10, 10, p.type === 'waterPlane' ? MESH_COUNT : 1, MESH_COUNT)

  const uniforms = {
    uTime: { value: startTime },
    uSpeed: { value: p.uSpeed },
    uLoop: { value: p.loop ? 1 : 0 },
    uLoopDuration: { value: p.loop || 5 },
    uNoiseDensity: { value: p.uDensity },
    uNoiseStrength: { value: p.uStrength },
    uFrequency: { value: p.uFrequency },
    uAmplitude: { value: p.uAmplitude },
    uC1: { value: hexToVec3(p.color1) },
    uC2: { value: hexToVec3(p.color2) },
    uC3: { value: hexToVec3(p.color3) },
  }

  const material = new THREE.MeshPhysicalMaterial({
    metalness: 0.2,
    roughness: 1 - (typeof p.reflection === 'number' ? p.reflection : 0.1),
    side: THREE.DoubleSide,
  })
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms)
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\n' + VERTEX_HEAD)
      .replace('#include <begin_vertex>', '#include <begin_vertex>\n' + vertexBody(p.type))
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform vec3 uC1;\nuniform vec3 uC2;\nuniform vec3 uC3;\nvarying vec3 vSgPos;')
      .replace('#include <color_fragment>', '#include <color_fragment>\n' + colorBody(p.type))
  }
  // One shader per mesh type (the GLSL differs by type).
  material.customProgramCacheKey = () => 'shadergradient-' + p.type

  const mesh = new THREE.Mesh(geometry, material)
  mesh.position.set(p.positionX, p.positionY, p.positionZ)
  mesh.rotation.set(d2r(p.rotationX), d2r(p.rotationY), d2r(p.rotationZ))
  scene.add(mesh)

  // grain: 'on' is a halftone pass in the original (radius 2, scatter 1). It is stateless, so seek-safe.
  let composer = null
  if (p.grain === 'on') {
    composer = new EffectComposer(renderer)
    composer.setPixelRatio(1)
    composer.setSize(width, height)
    composer.addPass(new RenderPass(scene, camera))
    composer.addPass(
      new HalftonePass({
        shape: 1, radius: 2, rotateR: Math.PI / 12, rotateB: (Math.PI / 12) * 2, rotateG: (Math.PI / 12) * 3,
        scatter: 1, blending: 1, blendingMode: 1, greyscale: false,
      }),
    )
  }

  function renderAt(time) {
    uniforms.uTime.value = startTime + (time || 0)
    if (composer) composer.render(0)
    else renderer.render(scene, camera)
  }

  if (options.autoSeek !== false) {
    window.addEventListener('hf-seek', (e) => renderAt(e.detail.time))
  }
  renderAt(window.__hfThreeTime || 0)
  return { renderAt, renderer, scene, camera, mesh, props: p }
}
