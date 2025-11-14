const fs = require('fs');
const path = require('path');

// Simple JavaScript syntax checker
function checkJSSyntax(content, filename) {
    try {
        // Extract JavaScript from <script> tags
        const scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
        let match;
        let hasErrors = false;
        
        while ((match = scriptRegex.exec(content)) !== null) {
            const jsCode = match[1];
            if (jsCode.trim()) {
                try {
                    // Basic syntax check using eval (not for production, just for checking)
                    new Function(jsCode);
                } catch (e) {
                    console.error(`❌ JavaScript syntax error in ${filename}:`);
                    console.error(`   ${e.message}`);
                    hasErrors = true;
                }
            }
        }
        
        return !hasErrors;
    } catch (e) {
        console.error(`❌ Error checking ${filename}: ${e.message}`);
        return false;
    }
}

// Check HTML files
const htmlFiles = ['index.html', 'debug.html', 'debug_auth.html', 'test.html'];

console.log('🔍 Checking JavaScript syntax in HTML files...');

let allGood = true;
htmlFiles.forEach(file => {
    if (fs.existsSync(file)) {
        const content = fs.readFileSync(file, 'utf8');
        const isGood = checkJSSyntax(content, file);
        if (isGood) {
            console.log(`✅ ${file} - JavaScript syntax OK`);
        } else {
            allGood = false;
        }
    } else {
        console.log(`⚠️  ${file} - File not found`);
    }
});

if (allGood) {
    console.log('\n✅ All HTML files have valid JavaScript syntax!');
} else {
    console.log('\n❌ Some files have JavaScript syntax errors.');
}
