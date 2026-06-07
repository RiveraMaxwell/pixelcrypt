/**
 * PixelCrypt Web - Client-side image XOR encryption
 * Replicates the Python version's logic using the same SHA-256 → seed → PRNG → XOR pipeline.
 * Uses a seeded xoshiro128** PRNG for deterministic keystream generation.
 */

(function () {
    "use strict";

    // === DOM Elements ===
    const fileInput = document.getElementById("fileInput");
    const browseBtn = document.getElementById("browseBtn");
    const dropZone = document.getElementById("dropZone");
    const fileInfo = document.getElementById("fileInfo");
    const keyInput = document.getElementById("keyInput");
    const toggleKey = document.getElementById("toggleKey");
    const strengthBar = document.getElementById("strengthBar");
    const strengthLabel = document.getElementById("strengthLabel");
    const encryptBtn = document.getElementById("encryptBtn");
    const decryptBtn = document.getElementById("decryptBtn");
    const downloadBtn = document.getElementById("downloadBtn");
    const verifyBtn = document.getElementById("verifyBtn");
    const downloadGroup = document.getElementById("downloadGroup");
    const previewArea = document.getElementById("previewArea");
    const canvasOriginal = document.getElementById("canvasOriginal");
    const canvasResult = document.getElementById("canvasResult");
    const status = document.getElementById("status");
    const tabs = document.querySelectorAll(".tab");

    // === State ===
    let originalImageData = null;
    let resultImageData = null;
    let currentView = "result";

    // === Seeded PRNG (xoshiro128**) ===
    // We need a deterministic PRNG seeded from the key to match Python's numpy.random behavior concept.
    // Note: This won't produce identical output to NumPy's PCG64, but uses the same principle.
    // For cross-compatibility with the Python version, both use the same seed derivation.

    function splitmix32(seed) {
        return function () {
            seed |= 0;
            seed = (seed + 0x9e3779b9) | 0;
            let t = seed ^ (seed >>> 16);
            t = Math.imul(t, 0x21f0aaad);
            t = t ^ (t >>> 15);
            t = Math.imul(t, 0x735a2d97);
            t = t ^ (t >>> 15);
            return t >>> 0;
        };
    }

    function xoshiro128ss(a, b, c, d) {
        return function () {
            const t = b << 9;
            let r = a * 5;
            r = ((r << 7) | (r >>> 25)) * 9;
            c ^= a;
            d ^= b;
            b ^= c;
            a ^= d;
            c ^= t;
            d = (d << 11) | (d >>> 21);
            return (r >>> 0) / 4294967296;
        };
    }

    function createRNG(seed) {
        const sm = splitmix32(seed);
        const a = sm();
        const b = sm();
        const c = sm();
        const d = sm();
        return xoshiro128ss(a, b, c, d);
    }

    // === SHA-256 Key to Seed ===
    async function keyToSeed(key) {
        const encoder = new TextEncoder();
        const data = encoder.encode(key);
        const hashBuffer = await crypto.subtle.digest("SHA-256", data);
        const hashArray = new Uint8Array(hashBuffer);

        // Convert first 4 bytes to a 32-bit integer (same concept as Python's mod 2^32)
        let seed = 0;
        for (let i = 0; i < 4; i++) {
            seed = (seed << 8) | hashArray[i];
        }
        return seed >>> 0;
    }

    // === Image Processing ===
    function processImageData(imageData, rng) {
        const data = imageData.data; // RGBA Uint8ClampedArray
        const result = new Uint8ClampedArray(data.length);

        for (let i = 0; i < data.length; i += 4) {
            // XOR RGB channels with random values
            result[i] = data[i] ^ Math.floor(rng() * 256);       // R
            result[i + 1] = data[i + 1] ^ Math.floor(rng() * 256); // G
            result[i + 2] = data[i + 2] ^ Math.floor(rng() * 256); // B
            result[i + 3] = data[i + 3]; // Alpha unchanged
        }

        return new ImageData(result, imageData.width, imageData.height);
    }

    async function processImage(sourceImageData, key) {
        const seed = await keyToSeed(key);
        const rng = createRNG(seed);
        return processImageData(sourceImageData, rng);
    }

    // === Key Strength ===
    function evaluateKeyStrength(key) {
        if (!key) return { score: 0, label: "", color: "" };

        let score = 0;
        const length = key.length;

        if (length >= 16) score += 40;
        else if (length >= 12) score += 30;
        else if (length >= 8) score += 20;
        else if (length >= 4) score += 10;

        const hasLower = /[a-z]/.test(key);
        const hasUpper = /[A-Z]/.test(key);
        const hasDigit = /\d/.test(key);
        const hasSpecial = /[^a-zA-Z0-9]/.test(key);

        const variety = [hasLower, hasUpper, hasDigit, hasSpecial].filter(Boolean).length;
        score += variety * 15;

        const uniqueChars = new Set(key).size;
        if (uniqueChars < length * 0.5) score -= 15;

        score = Math.max(0, Math.min(100, score));

        let label, color;
        if (score >= 80) { label = "Strong"; color = "var(--green)"; }
        else if (score >= 60) { label = "Good"; color = "var(--accent-light)"; }
        else if (score >= 40) { label = "Fair"; color = "var(--yellow)"; }
        else if (score >= 20) { label = "Weak"; color = "var(--red)"; }
        else { label = "Very Weak"; color = "var(--red)"; }

        return { score, label, color };
    }

    // === UI Helpers ===
    function showStatus(message, type) {
        status.textContent = message;
        status.className = "status " + type;
    }

    function clearStatus() {
        status.className = "status";
        status.textContent = "";
    }

    function updateButtons() {
        const hasImage = originalImageData !== null;
        const hasKey = keyInput.value.length > 0;
        encryptBtn.disabled = !(hasImage && hasKey);
        decryptBtn.disabled = !(hasImage && hasKey);
    }

    function loadImageToCanvas(img) {
        const ctx = canvasOriginal.getContext("2d");
        canvasOriginal.width = img.naturalWidth;
        canvasOriginal.height = img.naturalHeight;
        ctx.drawImage(img, 0, 0);
        originalImageData = ctx.getImageData(0, 0, img.naturalWidth, img.naturalHeight);

        // Reset result
        resultImageData = null;
        canvasResult.hidden = true;
        downloadGroup.style.display = "none";

        showPreview();
        updateButtons();
    }

    function showPreview() {
        const placeholder = previewArea.querySelector(".placeholder-text");
        if (placeholder) placeholder.remove();

        previewArea.classList.remove("side-by-side");
        canvasOriginal.hidden = true;
        canvasResult.hidden = true;

        if (currentView === "original" && originalImageData) {
            canvasOriginal.hidden = false;
        } else if (currentView === "result" && resultImageData) {
            canvasResult.hidden = false;
        } else if (currentView === "result" && originalImageData) {
            // Show original as placeholder if no result yet
            canvasOriginal.hidden = false;
        } else if (currentView === "side-by-side" && originalImageData) {
            previewArea.classList.add("side-by-side");
            canvasOriginal.hidden = false;
            if (resultImageData) canvasResult.hidden = false;
        }
    }

    // === File Loading ===
    function handleFile(file) {
        if (!file || !file.type.startsWith("image/")) {
            showStatus("Please select a valid image file.", "error");
            return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
            const img = new Image();
            img.onload = function () {
                loadImageToCanvas(img);
                const sizeKB = (file.size / 1024).toFixed(0);
                fileInfo.textContent = `${file.name} (${img.naturalWidth}×${img.naturalHeight}, ${sizeKB} KB)`;
                clearStatus();
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    // === Event Listeners ===

    // File input
    browseBtn.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", (e) => {
        if (e.target.files[0]) handleFile(e.target.files[0]);
    });

    // Drag & drop
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });
    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("dragover");
    });
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
    });

    // Key input
    keyInput.addEventListener("input", () => {
        const { score, label, color } = evaluateKeyStrength(keyInput.value);
        strengthBar.style.width = score + "%";
        strengthBar.style.background = color;
        strengthLabel.textContent = label;
        strengthLabel.style.color = color;
        updateButtons();
    });

    // Toggle key visibility
    toggleKey.addEventListener("click", () => {
        const isPassword = keyInput.type === "password";
        keyInput.type = isPassword ? "text" : "password";
    });

    // Tabs
    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            tabs.forEach((t) => t.classList.remove("active"));
            tab.classList.add("active");
            currentView = tab.dataset.view;
            showPreview();
        });
    });

    // Encrypt / Decrypt (same operation — XOR is symmetric)
    async function runProcess(mode) {
        if (!originalImageData || !keyInput.value) return;

        showStatus(`${mode === "encrypt" ? "Encrypting" : "Decrypting"}...`, "info");
        encryptBtn.disabled = true;
        decryptBtn.disabled = true;

        // Use setTimeout to allow UI to update
        setTimeout(async () => {
            try {
                const sourceData = originalImageData;
                resultImageData = await processImage(sourceData, keyInput.value);

                // Draw result to canvas
                canvasResult.width = resultImageData.width;
                canvasResult.height = resultImageData.height;
                const ctx = canvasResult.getContext("2d");
                ctx.putImageData(resultImageData, 0, 0);

                // Update UI
                currentView = "result";
                tabs.forEach((t) => t.classList.remove("active"));
                tabs[0].classList.add("active");
                showPreview();

                downloadGroup.style.display = "block";
                showStatus(
                    `${mode === "encrypt" ? "Encrypted" : "Decrypted"} successfully!`,
                    "success"
                );
            } catch (err) {
                showStatus("Error: " + err.message, "error");
            }
            updateButtons();
        }, 50);
    }

    encryptBtn.addEventListener("click", () => runProcess("encrypt"));
    decryptBtn.addEventListener("click", () => runProcess("decrypt"));

    // Download
    downloadBtn.addEventListener("click", () => {
        if (!resultImageData) return;
        canvasResult.toBlob((blob) => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "pixelcrypt_output.png";
            a.click();
            URL.revokeObjectURL(url);
        }, "image/png");
    });

    // Verify round-trip
    verifyBtn.addEventListener("click", async () => {
        if (!resultImageData || !keyInput.value) return;

        showStatus("Verifying round-trip...", "info");

        setTimeout(async () => {
            try {
                const roundTrip = await processImage(resultImageData, keyInput.value);

                // Compare with original
                const orig = originalImageData.data;
                const rt = roundTrip.data;
                let match = true;

                for (let i = 0; i < orig.length; i++) {
                    if (orig[i] !== rt[i]) {
                        match = false;
                        break;
                    }
                }

                if (match) {
                    showStatus("✓ Verification passed! Round-trip produces identical image.", "success");
                } else {
                    showStatus("✗ Verification failed. Decrypted output doesn't match original.", "error");
                }
            } catch (err) {
                showStatus("Verification error: " + err.message, "error");
            }
        }, 50);
    });
})();
