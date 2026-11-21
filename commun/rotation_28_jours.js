/* Éditions LÀ — rotation éditoriale proposée, non déployée.
 * Déterministe, sans tirage aléatoire et sans fuseau imposé.
 * Les dates sont celles du terminal de consultation.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ChronoLARotation = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  var LABELS = Object.freeze({ mot: 'LE MOT', fragment: 'LE FRAGMENT', extrait: 'L’EXTRAIT' });
  var pad = function (n) { return String(n).padStart(2, '0'); };

  function resolve(date, edition) {
    if (!(date instanceof Date) || Number.isNaN(date.getTime())) throw new TypeError('Date locale invalide');
    if (!edition || !Array.isArray(edition.pools) || edition.pools.length !== 12) throw new TypeError('Corpus incomplet');
    var minute = date.getHours() * 60 + date.getMinutes();
    var period = Math.floor(minute / 120);
    var withinPeriod = Math.floor((minute % 120) / 10);
    var dayOfMonth = date.getDate();
    // Days 29-31 borrow from the neighboring pool, avoiding same-time repeats.
    var bonus = dayOfMonth > 28;
    var selectedPeriod = bonus ? (period + 1) % 12 : period;
    var dayOffset = bonus ? dayOfMonth - 29 : dayOfMonth - 1;
    var position = (withinPeriod + dayOffset) % 28;
    var pool = edition.pools[selectedPeriod];
    if (!pool || !Array.isArray(pool.entries) || pool.entries.length !== 28) throw new TypeError('Tranche horaire incomplète');
    var entry = pool.entries[position];
    if (!entry) throw new TypeError('Rencontre manquante');
    return {
      hour: pad(date.getHours()) + ':' + pad(date.getMinutes()),
      slotStart: pad(Math.floor(minute / 60)) + ':' + pad(Math.floor((minute % 60) / 10) * 10),
      dateLocal: date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(dayOfMonth),
      editionId: edition.edition_id,
      period: period,
      selectedPool: pool.id,
      poolPosition: position,
      bonusDay: bonus,
      type: entry.type,
      label: LABELS[entry.type],
      text: entry.text,
      term: entry.type === 'mot' ? entry.term : null,
      grammarAndDomain: entry.type === 'mot' ? entry.grammar_and_domain : null,
      credit: entry.type === 'extrait' ? entry.author_credit : null,
      sourceTitle: entry.type === 'extrait' ? entry.source_title : null,
      id: entry.id,
      version: entry.version,
      entry: entry
    };
  }
  return { resolve: resolve, labels: LABELS };
});
