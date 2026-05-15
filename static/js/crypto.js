/**
 * Simple encryption utility for API headers
 * Uses AES-GCM with a user-provided secret key
 */

// Derive encryption key from secret
async function deriveKey(secret) {
    const encoder = new TextEncoder();
    const keyMaterial = await crypto.subtle.importKey(
        'raw',
        encoder.encode(secret),
        'PBKDF2',
        false,
        ['deriveKey']
    );
    return crypto.subtle.deriveKey(
        {
            name: 'PBKDF2',
            salt: encoder.encode('ThaiWordSalt'),
            iterations: 100000,
            hash: 'SHA-256'
        },
        keyMaterial,
        { name: 'AES-GCM', length: 256 },
        false,
        ['encrypt', 'decrypt']
    );
}

// Encrypt text
async function encryptText(text, secret) {
    if (!secret || !text) return text;
    try {
        const key = await deriveKey(secret);
        const encoder = new TextEncoder();
        const iv = crypto.getRandomValues(new Uint8Array(12));
        const encrypted = await crypto.subtle.encrypt(
            { name: 'AES-GCM', iv },
            key,
            encoder.encode(text)
        );
        // Combine IV + encrypted data and base64 encode
        const combined = new Uint8Array(iv.length + encrypted.byteLength);
        combined.set(iv);
        combined.set(new Uint8Array(encrypted), iv.length);
        return btoa(String.fromCharCode(...combined));
    } catch (e) {
        console.error('Encryption failed:', e);
        return text;
    }
}

// Decrypt text
async function decryptText(encryptedText, secret) {
    if (!secret || !encryptedText) return encryptedText;
    try {
        const key = await deriveKey(secret);
        const decoder = new TextDecoder();
        const combined = Uint8Array.from(atob(encryptedText), c => c.charCodeAt(0));
        const iv = combined.slice(0, 12);
        const data = combined.slice(12);
        const decrypted = await crypto.subtle.decrypt(
            { name: 'AES-GCM', iv },
            key,
            data
        );
        return decoder.decode(decrypted);
    } catch (e) {
        console.error('Decryption failed:', e);
        return encryptedText;
    }
}

// Get encrypted headers for API calls
async function getEncryptedHeaders() {
    const secret = localStorage.getItem('SECRET_KEY') || '';
    const dictApi = localStorage.getItem('DICT_API_URL') || '';
    const translateEndpoint = localStorage.getItem('TRANSLATE_API_ENDPOINT') || '';
    const translateToken = localStorage.getItem('TRANSLATE_AUTH_TOKEN') || '';
    const translateModel = localStorage.getItem('TRANSLATE_MODEL') || '';

    if (!secret) {
        // No encryption, return plain headers
        return {
            'X-Dict-API': dictApi,
            'X-Translate-Endpoint': translateEndpoint,
            'X-Translate-Token': translateToken,
            'X-Translate-Model': translateModel,
        };
    }

    // Encrypt sensitive values
    const [encDict, encEndpoint, encToken] = await Promise.all([
        encryptText(dictApi, secret),
        encryptText(translateEndpoint, secret),
        encryptText(translateToken, secret),
    ]);

    return {
        'X-Dict-API': encDict,
        'X-Translate-Endpoint': encEndpoint,
        'X-Translate-Token': encToken,
        'X-Translate-Model': translateModel,
        'X-Encrypted': 'true',
    };
}
