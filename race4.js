/* Hygie Race 4 — révélation des sections au scroll (robuste, jamais de contenu bloqué). */
(function(){
  var els = [].slice.call(document.querySelectorAll('.reveal'));
  if(!els.length) return;
  document.body.classList.add('js-anim');
  function reveal(el){ el.classList.add('in'); }
  function check(){
    var h = window.innerHeight || 800;
    for(var i=0;i<els.length;i++){
      var el = els[i];
      if(el.classList.contains('in')) continue;
      var r = el.getBoundingClientRect();
      if(r.top < h*0.9 && r.bottom > 0) reveal(el);
    }
  }
  window.addEventListener('scroll', check, {passive:true});
  window.addEventListener('resize', check);
  check();
  setTimeout(check, 250);
  setTimeout(function(){ els.forEach(reveal); }, 3000);
})();
