#!/usr/bin/env node

/**
 * Helper script to compile all .mmd Mermaid files in docs/assets/diagrams/ into .svg vector assets.
 * Usage: node scripts/render_diagrams.js
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const diagramDir = path.join(__dirname, '..', 'docs', 'assets', 'diagrams');
const puppeteerConfig = path.join(__dirname, '..', 'docs', 'assets', 'diagrams', '.puppeteer-config.json');

// Write puppeteer config with --no-sandbox flag for Linux CI/CD compatibility
fs.writeFileSync(puppeteerConfig, JSON.stringify({
  args: ['--no-sandbox', '--disable-setuid-sandbox']
}));

console.log('Rendering Mermaid diagrams in:', diagramDir);

const files = fs.readdirSync(diagramDir);
const mmdFiles = files.filter(f => f.endsWith('.mmd'));

mmdFiles.forEach(file => {
  const mmdPath = path.join(diagramDir, file);
  const svgPath = path.join(diagramDir, file.replace(/\.mmd$/, '.svg'));
  console.log(`Compiling ${file} -> ${path.basename(svgPath)}...`);
  
  const cmd = `npx -y @mermaid-js/mermaid-cli -p "${puppeteerConfig}" -i "${mmdPath}" -o "${svgPath}" -b transparent`;
  try {
    execSync(cmd, { stdio: 'inherit' });
    console.log(`Successfully generated ${path.basename(svgPath)}`);
  } catch (err) {
    console.error(`Failed to compile ${file}:`, err.message);
  }
});

// Clean up temp config
if (fs.existsSync(puppeteerConfig)) {
  fs.unlinkSync(puppeteerConfig);
}

console.log('Diagram rendering complete.');
