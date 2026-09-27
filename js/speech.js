// French pronunciation with the browser's built-in speech synthesis.

import { settings } from './store.js';

const synth = 'speechSynthesis' in window ? window.speechSynthesis : null;
let voices = [];
const listeners = new Set();

export const supported = !!synth;

function refresh() {
  voices = synth ? synth.getVoices().filter((v) => /^fr([-_]|$)/i.test(v.lang)) : [];
  listeners.forEach((fn) => fn(voices));
}

if (synth) {
  refresh();
  synth.addEventListener?.('voiceschanged', refresh);
  // Some browsers populate voices lazily and never fire the event.
  setTimeout(refresh, 400);
  setTimeout(refresh, 1500);
}

export function frenchVoices() {
  return voices;
}

export function onVoices(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

const QUALITY = /(natural|neural|premium|enhanced|google|siri|amélie|amelie|thomas|audrey|aurélie|marie|julie|paul|hortense|denise|henri|eloise|vivienne)/i;

export function currentVoice() {
  const s = settings();
  if (s.voice) {
    const v = voices.find((v) => v.voiceURI === s.voice);
    if (v) return v;
  }
  const pool = voices.filter((v) => /fr[-_]FR/i.test(v.lang));
  const list = pool.length ? pool : voices;
  return (
    list.find((v) => QUALITY.test(v.name) && v.localService) ||
    list.find((v) => QUALITY.test(v.name)) ||
    list.find((v) => v.default) ||
    list[0] ||
    null
  );
}

// Must be called inside a user gesture once so that later speech is allowed (iOS).
export function unlock() {
  if (!synth) return;
  try {
    const u = new SpeechSynthesisUtterance(' ');
    u.volume = 0;
    synth.speak(u);
  } catch {}
}

export function stop() {
  synth?.cancel();
}

// Speaks the text; resolves when finished (or after a safety timeout).
export function speak(text, { rate } = {}) {
  return new Promise((resolve) => {
    if (!synth) return resolve(false);
    synth.cancel();
    const u = new SpeechSynthesisUtterance(text);
    const v = currentVoice();
    if (v) u.voice = v;
    u.lang = v?.lang || 'fr-FR';
    u.rate = rate ?? settings().rate;
    u.pitch = 1;
    let done = false;
    const finish = (ok) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      resolve(ok);
    };
    const timer = setTimeout(() => finish(true), 5000);
    u.onend = () => finish(true);
    u.onerror = () => finish(false);
    // Chrome occasionally drops an utterance issued right after cancel().
    setTimeout(() => synth.speak(u), 30);
  });
}
