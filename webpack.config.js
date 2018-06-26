module.exports = {
	context: __dirname,
	entry: "./static/js/index.js",
	output: {
		path: __dirname + "/static/dist",
		filename: "bundle.js"
	},
	stats: {
		warnings: false
	}
}