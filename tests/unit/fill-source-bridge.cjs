// Strip ONLY the five explicit Fill metadata/dispatch hooks; all other bytes
// remain covered by earlier baseline integrity tests.
function withoutFillHooks(s){return s
 .replace('if(window.HappyFill)window.HappyFill.remember(history.at(-1),[...history,...redo]);','')
 .replace('   if(window.HappyFill)window.HappyFill.restore(src);\n','')
 .replace(' // PATTERN-DISPATCH: normal solid fills retain the accepted implementation.\n if(window.HappyFill && window.HappyFill.needsPatternPath())return window.HappyFill.paint(ctx,canvas,x0,y0,fillHex,W());\n','')
 .replace('function clearAll(){if(window.HappyFill)window.HappyFill.reset();','function clearAll(){')
 .replace('ctx.drawImage(prepared,0,0);ctx.restore();if(window.HappyFill)window.HappyFill.reset();snap();','ctx.drawImage(prepared,0,0);ctx.restore();snap();');}
module.exports={withoutFillHooks};
