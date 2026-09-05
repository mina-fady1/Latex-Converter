const mathjax = require('mathjax');
const fs = require('fs');

async function getInputs() {
    let latex = '';
    let color = '#ff003c';
    let display = true;

    const args = process.argv.slice(2);
    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg === '--latex' && i + 1 < args.length) {
            latex = args[++i];
        } else if (arg === '--color' && i + 1 < args.length) {
            color = args[++i];
        } else if (arg === '--display' && i + 1 < args.length) {
            display = args[++i].toLowerCase() !== 'false';
        } else if (arg.startsWith('{')) {
            try {
                const parsed = JSON.parse(arg);
                if (parsed.latex !== undefined) latex = parsed.latex;
                if (parsed.color !== undefined) color = parsed.color;
                if (parsed.display !== undefined) display = Boolean(parsed.display);
            } catch (e) {}
        }
    }

    if (!latex && !process.stdin.isTTY) {
        try {
            const stdinData = fs.readFileSync(0, 'utf-8');
            if (stdinData.trim()) {
                try {
                    const parsed = JSON.parse(stdinData);
                    if (parsed.latex !== undefined) latex = parsed.latex;
                    if (parsed.color !== undefined) color = parsed.color;
                    if (parsed.display !== undefined) display = Boolean(parsed.display);
                } catch (e) {
                    latex = stdinData.trim();
                }
            }
        } catch (e) {}
    }

    return { latex, color, display };
}

async function render() {
    const { latex, color, display } = await getInputs();

    if (!latex || !latex.trim()) {
        console.error('Error: No LaTeX input provided.');
        process.exit(1);
    }

    try {
        const MathJax = await mathjax.init({
            loader: {
                load: ['input/tex', 'output/svg', '[tex]/all-packages']
            },
            tex: {
                packages: {'[+]': ['all-packages']}
            },
            svg: {
                fontCache: 'none' // Embed direct <path> elements instead of <use> references
            }
        });

        const node = MathJax.tex2svg(latex, { display: display });
        
        // Extract raw <svg>...</svg> without <mjx-container> wrapper
        let svgOutput = MathJax.startup.adaptor.innerHTML(node);

        if (!svgOutput || svgOutput.includes('data-mjx-error') || svgOutput.includes('merror')) {
            console.error('MathJax Render Error: Invalid LaTeX formula syntax.');
            process.exit(1);
        }

        // 1. Convert 'ex' units to 'px' for high-precision vector mapping
        svgOutput = svgOutput.replace(/width="([0-9.]+)ex"/g, (match, val) => {
            const px = (parseFloat(val) * 16.0).toFixed(2);
            return `width="${px}px"`;
        });
        svgOutput = svgOutput.replace(/height="([0-9.]+)ex"/g, (match, val) => {
            const px = (parseFloat(val) * 16.0).toFixed(2);
            return `height="${px}px"`;
        });

        // 2. CRITICAL FOR POWERPOINT UNGROUPING & SHAPE OUTLINES:
        // Set stroke="none" stroke-width="0" stroke-opacity="0" directly on <path> and solid <rect> elements.
        // PowerPoint's shape converter automatically adds a 0.75pt/1pt outline if stroke attributes are absent or inherited.
        // Explicitly tagging stroke="none" stroke-width="0" stroke-opacity="0" instructs PowerPoint to import shapes with "No Line" (0pt border).
        svgOutput = svgOutput.replace(/stroke="currentColor"/g, 'stroke="none"');
        svgOutput = svgOutput.replace(/fill="currentColor"/g, `fill="${color}"`);

        svgOutput = svgOutput.replace(/<path /g, `<path stroke="none" stroke-width="0" stroke-opacity="0" fill="${color}" `);
        
        // Handle <rect> tags appropriately:
        // - Enclosure boxes (e.g. \boxed, menclose) have fill="none" and stroke-width. They MUST have stroke="${color}" and keep fill="none" without duplicate attributes.
        // - Solid bars (fraction lines, square root vinculum) have no existing fill/stroke attributes, so set fill="${color}" and stroke="none".
        svgOutput = svgOutput.replace(/<rect\b([^>]*)>/g, (match, attrs) => {
            if (attrs.includes('fill="none"')) {
                let newAttrs = attrs;
                if (!newAttrs.includes('stroke=')) {
                    newAttrs = ` stroke="${color}" stroke-opacity="1"` + newAttrs;
                } else {
                    newAttrs = newAttrs.replace(/stroke="[^"]*"/, `stroke="${color}"`);
                }
                return `<rect${newAttrs}>`;
            } else {
                return `<rect stroke="none" stroke-width="0" stroke-opacity="0" fill="${color}"${attrs}>`;
            }
        });

        // Apply color styles to svg root
        if (svgOutput.includes('style="')) {
            svgOutput = svgOutput.replace('style="', `style="color: ${color}; fill: ${color}; `);
        } else {
            svgOutput = svgOutput.replace('<svg', `<svg style="color: ${color}; fill: ${color};"`);
        }

        // 3. Add standard XML declaration header for standalone SVG validity
        if (!svgOutput.startsWith('<?xml')) {
            svgOutput = '<?xml version="1.0" encoding="UTF-8"?>\n' + svgOutput;
        }

        process.stdout.write(svgOutput);
        process.exit(0);
    } catch (err) {
        console.error('MathJax Error:', err.message || err);
        process.exit(1);
    }
}

render();
