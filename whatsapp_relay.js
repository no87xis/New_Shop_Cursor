const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());

// WhatsApp Client
let client = null;
let isReady = false;
let qrCode = null;

// Initialize WhatsApp client
function initWhatsApp() {
    client = new Client({
        authStrategy: new LocalAuth({
            clientId: 'sirius-group-wa'
        }),
        puppeteer: {
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        }
    });

    client.on('qr', (qr) => {
        console.log('QR Code received');
        qrCode = qr;
        qrcode.generate(qr, { small: true });
        
        // Save QR code to file
        fs.writeFileSync('/tmp/wa_qr.txt', qr);
    });

    client.on('ready', () => {
        console.log('WhatsApp client is ready!');
        isReady = true;
        qrCode = null;
    });

    client.on('authenticated', () => {
        console.log('WhatsApp client authenticated');
    });

    client.on('auth_failure', (msg) => {
        console.error('Authentication failed:', msg);
        isReady = false;
    });

    client.on('disconnected', (reason) => {
        console.log('WhatsApp client disconnected:', reason);
        isReady = false;
    });

    client.initialize();
}

// Routes
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        whatsapp_ready: isReady,
        qr_available: !!qrCode,
        timestamp: new Date().toISOString()
    });
});

app.get('/qr', (req, res) => {
    if (qrCode) {
        res.json({ qr: qrCode });
    } else if (isReady) {
        res.json({ message: 'WhatsApp is already connected' });
    } else {
        res.status(404).json({ error: 'QR code not available' });
    }
});

app.post('/send', async (req, res) => {
    try {
        if (!isReady) {
            return res.status(503).json({ 
                error: 'WhatsApp client not ready',
                qr_available: !!qrCode
            });
        }

        const { phone, message } = req.body;
        
        if (!phone || !message) {
            return res.status(400).json({ 
                error: 'Phone and message are required' 
            });
        }

        // Normalize phone number
        let normalizedPhone = phone.replace(/\D/g, '');
        if (!normalizedPhone.startsWith('375')) {
            normalizedPhone = '375' + normalizedPhone;
        }
        normalizedPhone = normalizedPhone + '@c.us';

        // Send message
        const result = await client.sendMessage(normalizedPhone, message);
        
        res.json({
            success: true,
            messageId: result.id._serialized,
            phone: phone,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Error sending message:', error);
        res.status(500).json({ 
            error: 'Failed to send message',
            details: error.message
        });
    }
});

app.get('/status', (req, res) => {
    res.json({
        ready: isReady,
        qr_available: !!qrCode,
        client_state: client ? 'initialized' : 'not_initialized'
    });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`WhatsApp Relay server running on port ${PORT}`);
    initWhatsApp();
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('Shutting down WhatsApp Relay...');
    if (client) {
        client.destroy();
    }
    process.exit(0);
});