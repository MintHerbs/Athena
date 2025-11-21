
const cheerio = require('cheerio');



(async () => {
  const url = 'https://www.example.com';
  const response = await fetch(url);

  const $ = cheerio.load(await response.text());
  console.log($.html());

  const title = $('h1').text();
const text = $('p').text();
const link = $('a').attr('href');

console.log(title);
console.log(text);
console.log(link);

})();

