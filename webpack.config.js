var webpack = require('webpack');

module.exports = {
	context: __dirname,
	entry: "./static/js/index.js",
	output: {
		path: __dirname + "/static/dist",
		filename: "bundle.js"
	},
	stats: {
		warnings: false
	},
	module: {
		rules: [
			{
				test: /\.css$/, 
				loader: 'style-loader!css-loader'
			},
			{
				test : /\.(woff(2)?|ttf|eot|svg)(\?v=\d+\.\d+\.\d+)?$/,
				use: [{
					loader: 'file-loader',
					options: {
						name: '[name].[ext]',
						outputPath: 'fonts/',
						publicPath: '/static/dist/fonts/'
					}
				}]
			},
			{
				test : /\.png$/,
				use: [{
					loader: 'file-loader',
					options: {
						name: '[name].[ext]',
						outputPath: 'img/',
						publicPath: '/static/dist/img/'
					}
				}]
			}
		]
	}
}
