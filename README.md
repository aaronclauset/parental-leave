<script src='//d3js.org/d3.v4.js'></script>
<style type="text/css">
body {
	font-family: "Helvetica";
}
	
div.tooltip {	
	position: absolute;			
	text-align: left;			
	padding: 4px;				
	font: 12px sans-serif;		
	background: #eee;				
}

h2 {
	font-weight: 100;
	font-size: 2em; 
}

h3 {
	padding-top: 10px; 
	margin-top: 0px;
}

h4 {
	font-size: 1em;
	display: inline;
	clear: none;
	padding-right: 0.5em;
	height: 20px;
}

.controls {
	padding-bottom: 10px;
}

form {
	display: inline-block;
}

.title {
	font-weight: bold;
}

.legend_item {
	font-size: 1.3em;
}

#color_legend {
	height: 20px;
}

a:hover, a:focus {
	font-weight: 400; 
}

a {
	font-weight: 400;
}
</style>

# Motivation

Inspired in part by a study of university parental leave policies by [Antecol et al.](https://docs.google.com/viewer?a=v&pid=sites&srcid=ZGVmYXVsdGRvbWFpbnxzdGVhcm5zamV8Z3g6NDE0NTM4MTBhYjBmYjhmYw) ([New York Times](https://www.nytimes.com/2016/06/26/business/tenure-extension-policies-that-put-women-at-a-disadvantage.html), [Inside HigherEd](https://www.insidehighered.com/news/2016/06/27/stopping-tenure-clock-may-help-male-professors-more-female-study-finds)), we recently collected the paid<sup>1</sup> parental leave policies for tenure-track faculty<sup>2</sup> at 205 research universities in the US and Canada. The purpose of this post is to share the data we collected, highlight the complexity of many such policies, and share some preliminary analyses.

# Methods

We collected parental leave policies of the 205 universities on the [Computing Research Association's](https://cra.org/about/) [Forsythe list](http://archive.cra.org/reports/forsythe.html) of PhD-granting institutions in the US and Canada, which reflects our specific interest in computing departments.

For each university, we Googled "[university name] faculty parental leave policy" or "[university name] faculty handbook" and recorded the institution's policy for female and male faculty separately, noting the duration of paid leave and form of relief granted, if stated (e.g. relief from just teaching, all duties, etc.). Several universities offer disability leave that may apply to some new parents.<sup>3</sup> Here, we focused our efforts on recording policies specifically for parental leave. This process took about 5 minutes per university and recovered policies for 197 of the 205 target institutions (96%). The eight missing policies correspond to institutions whose faculty handbooks are either not available online or require an employee login. 

# Parental leave data

We've compiled the resulting dataset into a [spreadsheet](https://github.com/aaronclauset/parental-leave/blob/master/parental_leave_policies.tsv), included in this GitHub project. 

* If you spot an error or know the policy at an institution that isn't listed, please let us know using this [feedback form](https://goo.gl/forms/uZAVXaqRGpF3AjNS2). 
* If you can instead confirm that we correctly recorded the policy at your institution, please let us know [here](https://goo.gl/forms/O6gHXZVho2QZmnL13). 

Your feedback will help ensure that this dataset is as accurate as possible.

One immediate takeaway from our data collection effort is that university parental leave policies, as written, can be difficult to understand. For example, several policies we found state that if both parents are tenure-track faculty, they must share the parental leave benefit (e.g. [Toyota Technical Institute](http://www.ttic.edu/dl/faculty_handbook.pdf)). Other policies describe a short amount of time off at full-pay with relief from all duties, followed by a longer time off with relief only from some duties (e.g. Princeton's [leave](https://dof.princeton.edu/working-princeton/benefits/paid-leave-childbearing-for-faculty) and [workload relief](https://dof.princeton.edu/working-princeton/benefits/workload-relief-new-parents-for-faculty) policies). For consistency across universities, we recorded both types of policies as the longer amount of relief only. Confusingly, many parental leave policies are written in terms of “primary caregiver” benefits (e.g. [Michigan Technological University](https://www.mtu.edu/hr/current/benefits/docs/parental-leave.pdf)) without defining whether both parents can have that role or only one, as well as fractional amounts of salaries to be received (e.g. [University of Utah](https://regulations.utah.edu/academics/6-315.php)). Other policies are simple in structure and simple to understand, e.g., both parents can take 1 semester of paid leave with full relief of duties (e.g., [University of Colorado Boulder](https://www.cu.edu/ope/aps/5019)).

# Data summary

* About 60% of institutions have some form of paid parental leave for new mothers or fathers.
* For universities with paid leave policies, the average duration is 14.2 weeks for women and 11.6 weeks for men.
* Among universities that offer paid leave, 68.3% have gender-neutral policies (same leave for men and women).
* Private institutions have slightly longer leaves (by about 2 weeks).
* The relationship between an institution's prestige and its leave policies is complex and will require careful analysis.

<p align="center" style="font-weight: 400;"><a href="#analysis">Read on below the visualization for more details.</a></p>

# Visualization
<a name="visualization"></a>
Explore the data. The university ranking option sorts by the inferred prestige of a university according to its Computer Science department (details [here](http://advances.sciencemag.org/content/1/1/e1400005)). Regions are U.S. Census regions plus Canada. All data points represent university-provided paid parental leaves only. Hover over a data point to see more details on the policy, including its primary source.

<div class="controls">
	<h4 class="title">Sort by: </h4>
	<button type="button" onclick="rearrange('sorted_by_name')">University Name</button>
	<button type="button" onclick="rearrange('sorted_by_prestige')">University Rank (CS)</button>
	<button type="button" onclick="rearrange('sorted_by_women')">Women's Leave</button>
	<button type="button" onclick="rearrange('sorted_by_men')">Men's Leave</button>
</div>
<div class="controls">
	<form autocomplete="off">
		<h4 class="title">Color by:</h4>
		<label>
		    <input type="radio" name="highlight" value="none" checked="checked"/>None
		</label>
		<label>
		    <input type="radio" name="highlight" value="pubpriv"/>Private/Public Status
		</label>
		<label>
		    <input type="radio" name="highlight" value="loc"/>Region
		</label>
	</form>
</div>
<div id="color_legend" class="controls"></div>

<h3></h3>

<!-- Begin D3 Javascript -->
<script type="text/javascript">
    // Globals 
    var TEXT_POS = 175;
    var TEXT_PAD = 10;
    var DEFAULT_F_COLOR = "#67C080";
    var DEFAULT_M_COLOR = "#202020";
    var PRIVATE_COLOR = "#B074E8"
    var PUBLIC_COLOR = "#202020";
    var REGION_COLORS = { "Midwest": "#AB4ADB", 
    					  "Northeast": "#077187",
    					  "South": "#CCA43B",
    					  "West": "#5BBA6F",
    					  "Canada": "#DB3A34"};
    var DEFAULT_MARKER_COLOR = "#999999";
    var TRANSITION_DURATION = 1000;

    // Setup data
    var tsvdata = [];
    var sortby = "sorted_by_name"; 

    // Setup settings for graphic
    var canvas_width = 550;
    var canvas_height = 2500;
    var yPadding = 60;
    var xPadding = 200;
    var xScale;
    var yScale;
    var shapes; 
    var texts;
    var xticks = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50];

    // Presorting function
    function presort_by(data, by, name, isNumeric)
    {
    	// Default to alphabetical if values are the same.
    	var to_sort = []
    	if (isNumeric) {
			for (var i = 0; i < data.length; i++) 
			{ to_sort.push([parseFloat(data[i][by]), i, data[i]["short_name"]]);}
			to_sort.sort(function(left, right) {
				if (left[0] != right[0])
						return left[0] > right[0] ? -1 : 1; 
				else
					return left[2] < right[2] ? -1 : 1; });
    	}
		else {
			for (var i = 0; i < data.length; i++) 
			{ to_sort.push([data[i][by], i, data[i]["short_name"]]); }
			to_sort.sort(function(left, right) {
				
				if (left[0] != right[0])
						return left[0] < right[0] ? -1 : 1;
				else
					return left[2] < right[2] ? -1 : 1; });
		}

		// Fill in sorted and SCALED values
		for (i=0; i<data.length; i++) { 
			data[to_sort[i][1]][name] = yScale(i); 
		}
		return;
    }

    // Tooltip functions
    function make_tooltip(d) {	

    	var source_link; 
    	if ("link" in d && d.link.includes("http"))
    		source_link = "<br />[<a target='_blank' href='" + d.link + "'>source</a>]";
    	else
    		source_link = "";

        div.transition()		
            .duration(200)		
            .style("opacity", .9);		
        div.html("<span class='title'>" + d.short_name + "</span>"
        	+ "<br />Women: " + d.paid_leave_weeks_woman + " weeks"
        	+ "<br />Men: " + d.paid_leave_weeks_man + " weeks"
        	+ source_link)	
            .style("left", (d3.event.pageX + 10) + "px")		
            .style("top", (d3.event.pageY - 28) + "px");	
     }

     function hide_tooltip(d) {		
     	div.transition()		
            .duration(500)	
            .delay(1000)	
            .style("opacity", 0);	
    }
    
    // Create SVG element
    var svg = d3.select("h3")
        .append("svg")
        .attr("width", canvas_width)
        .attr("height", canvas_height)

    // Tooltip 
    var div = d3.select("body").append("div")	
    		.attr("class", "tooltip")				
    		.style("opacity", 0);

		// Load data and build the figure
	d3.tsv("parental_leave_policies.tsv", function(data) {

		// Only show universities where we found a policy
		data = data.filter(function(entry) { return entry.missing == 0; });

		// Create scale functions
        xScale = d3.scaleLinear()
            .domain([0, 52])
            .range([TEXT_POS+TEXT_PAD, canvas_width]); 

        yScale = d3.scaleLinear() 
            .domain([0, data.length])
            .range([yPadding, canvas_height - yPadding/2]);
    	
    	/*
			Helper variables:
				- rev_rank: reverses rank to sort most prestigious to top
				- f_color: variable for coloring the female marker
				- m_color: variable for coloring the male marker
    	*/
		for (var i = 0; i < data.length; i++) {
			data[i].rev_rank = -parseFloat(data[i].rank); 
			data[i].f_color = DEFAULT_F_COLOR;
			data[i].m_color = DEFAULT_M_COLOR;
		}

		// Pre-calculate sorted indicies
		presort_by(data, "paid_leave_weeks_woman", "sorted_by_women", true)
		presort_by(data, "paid_leave_weeks_man", "sorted_by_men", true)
		presort_by(data, "rev_rank", "sorted_by_prestige", true)
		presort_by(data, "short_name", "sorted_by_name", false)

        // Custom grid
        for (i=0; i<xticks.length; i++)
        {
        	svg.append("line")
        		.style("stroke", "gray")	
        		.style("stroke-dasharray", ("1, 3"))
        		.attr("stroke-width", ".5")
        		.attr("x1", xScale(xticks[i]))
        		.attr("x2", xScale(xticks[i]))
        		.attr("y1", yScale(0) - 15)
        		.attr("y2", yScale(data.length));

        	svg.append("text")
        		.attr("color", DEFAULT_M_COLOR)
        		.attr("x", xScale(xticks[i]))
	            	.attr("y", yScale(0) - 20)
            		.attr("font-weight", 100)
        	    	.attr("text-anchor", "middle")
	            	.attr("font-size", "14px")
            		.text(xticks[i]);
		
		svg.append("text")
        		.attr("color", DEFAULT_M_COLOR)
        		.attr("x", xScale(xticks[i]))
        	    	.attr("y", yScale(data.length + 1.5))
	            	.attr("font-weight", 100)
            		.attr("text-anchor", "middle")
        	    	.attr("font-size", "14px")
	            	.text(xticks[i]);
        }

        // Title and legend
		svg.append("text")
    		.attr("x", xScale(0))
        	.attr("y", yScale(0) - 45)
        	.attr("color", DEFAULT_M_COLOR)
        	.attr("font-weight", 100)
        	.attr("text-anchor", "start")
        	.attr("font-size", "16px")
        	.text("Paid Leave Duration (weeks)");	

    	svg.append("circle")
    		.attr("class", "f_marker")
    		.attr("cx", xScale(35))
    		.attr("cy", yScale(0) - 50)
    		.attr("fill", "#fff")
            .attr("stroke", "#67C080")
            .attr("stroke-width", "2")
            .attr("r", 3.5);
        svg.append("text")
    		.attr("x", xScale(36))
        	.attr("y", yScale(0) - 45)
        	.attr("font-weight", 100)
        	.attr("text-anchor", "start")
        	.attr("font-size", "14px")
        	.attr("color", DEFAULT_M_COLOR)
        	.text("Women");

        svg.append("line")
        	.attr("class", "m_marker")
        	.attr("stroke", "black")
        	.attr("stroke-width", "1.25")
        	.attr("x1", xScale(45)-3)
        	.attr("x2", xScale(45)+3)
        	.attr("y1", yScale(0)-50-3)
        	.attr("y2", yScale(0)-50+3);
        svg.append("line")
        	.attr("class", "m_marker")
        	.attr("stroke", "black")
        	.attr("stroke-width", "1.25")
        	.attr("x1", xScale(45)-3)
        	.attr("x2", xScale(45)+3)
        	.attr("y1", yScale(0)-50+3)
        	.attr("y2", yScale(0)-50-3);
       	svg.append("text")
    		.attr("x", xScale(46))
        	.attr("y", yScale(0) - 45)
        	.attr("font-weight", 100)
        	.attr("text-anchor", "start")
        	.attr("font-size", "14px")
        	.attr("color", DEFAULT_M_COLOR)
        	.text("Men");

        // Create all of our markers
        shapes = svg.selectAll(".shapes").data(data).enter();

        // Line connecting the two markers
        shapes.append("line")
        	.style("stroke", "gray")
        	.attr("stroke-width", ".5")
        	.attr("class", "linesc movey")
        	.attr("x1", function(d, i) { return xScale(d.paid_leave_weeks_man); })
        	.attr("x2", function(d, i) { return xScale(d.paid_leave_weeks_woman); })
        	.attr("y1", function(d, i) { return d[sortby]; })
        	.attr("y2", function(d, i) { return d[sortby]; });

        // Women (circles)
        shapes.append("circle")
    		.attr("cx", function(d, i) { return xScale(d.paid_leave_weeks_woman); })
    		.attr("cy", function(d, i) { return d[sortby]; })
    		.attr("fill", "#fff")
            .attr("stroke", function(d, i) { return d.f_color; })
            .attr("stroke-width", "2")
            .attr("r", 3.5)
            .attr("class", "dots movey")
            .on("mouseover", function(d) { make_tooltip(d); })					
    		.on("mouseout", function(d) { hide_tooltip(d); });

        // Men (draw X as two lines)
        shapes.append("line")
        	.attr("stroke", function(d, i) { return d.m_color; })
        	.attr("stroke-width", "1.25")
        	.attr("class", "x1")
        	.on("mouseover", function(d) { make_tooltip(d); })					
    		.on("mouseout", function(d) { hide_tooltip(d); })
        	.attr("x1", function(d, i) { return xScale(d.paid_leave_weeks_man)-3; })
        	.attr("x2", function(d, i) { return xScale(d.paid_leave_weeks_man)+3; })
        	.attr("y1", function(d, i) { return d[sortby]-3; })
        	.attr("y2", function(d, i) { return d[sortby]+3; });
        shapes.append("line")
        	.attr("stroke", function(d, i) { return d.m_color; })
        	.attr("stroke-width", "1.25")
        	.attr("class", "x2")
        	.on("mouseover", function(d) { make_tooltip(d); })					
    		.on("mouseout", function(d) { hide_tooltip(d); })
        	.attr("x1", function(d, i) { return xScale(d.paid_leave_weeks_man)-3; })
        	.attr("x2", function(d, i) { return xScale(d.paid_leave_weeks_man)+3; })
        	.attr("y1", function(d, i) { return d[sortby]+3; })
        	.attr("y2", function(d, i) { return d[sortby]-3; });

        // University labels
        texts = shapes.append("text")
            .attr("class", "names movey")
            .attr("color", function(d) { return d.m_color; })
            .attr("x", function(d, i) { return TEXT_POS; })
            .attr("y", function(d, i) { return d[sortby]; })
            .text(function(d) { return d.short_name; })
            .attr("font-weight", "100")
            .attr("alignment-baseline", "central")
            .attr("text-anchor", "end")
            .attr("font-size", "11px");

    	// Save data to global variable
        tsvdata = data;
	});

    function rearrange(by, force_update = false) {
		
		// Bail if no changes needed
		if (sortby == by && !force_update) { return; }

		// Update sorting variable
		sortby = by; 

        // Update female markers...
        svg.selectAll(".dots")
        .transition()
        .duration(TRANSITION_DURATION)
        .delay(function(d, i) { return i / tsvdata.length * 500; })
        .attr("stroke", function(d, i) { return d.f_color; })
        .attr("cy", function(d, i) { return d[sortby]; })

        // ...connecting lines...
		svg.selectAll(".linesc")
		.transition()
		.duration(TRANSITION_DURATION)
		.delay(function(d, i) { return i / tsvdata.length * 500; })
		.attr("y1", function(d, i) { return d[sortby]; })
		.attr("y2", function(d, i) { return d[sortby]; });

        // ...male markers...
    	svg.selectAll(".x1")
        .transition()
        .duration(TRANSITION_DURATION)
        .delay(function(d, i) { return i / tsvdata.length * 500; })
        .attr("stroke", function(d, i) { return d.m_color; })
    	.attr("y1", function(d, i) { return d[sortby]-3; })
    	.attr("y2", function(d, i) { return d[sortby]+3; });
    	svg.selectAll(".x2")
        .transition()
        .duration(TRANSITION_DURATION)
        .delay(function(d, i) { return i / tsvdata.length * 500; })
        .attr("stroke", function(d, i) { return d.m_color; })
    	.attr("y1", function(d, i) { return d[sortby]+3; })
    	.attr("y2", function(d, i) { return d[sortby]-3; });

        // ...and names of the universities.
		svg.selectAll(".names")
        .transition()
        .duration(TRANSITION_DURATION)
        .delay(function(d, i) { return i / tsvdata.length * 500; })
        .style('fill',  function(d, i) { return d.m_color; } )
        .attr("y", function(d, i) { return d[sortby]; });
    }

    // Radio button controls (for selecting coloring options)
    d3.selectAll("input[name='highlight']").on("change", 
    	function() {

		// For updating the legend
		var f_marker_color = DEFAULT_MARKER_COLOR;
		var m_marker_color = DEFAULT_MARKER_COLOR; 

		// If coloring by public/private status
    	if (this.value == "pubpriv")
    	{
        	for (var i=0; i<tsvdata.length; i++){
    			if (tsvdata[i].is_private == 1)
    			{
        			tsvdata[i].f_color = PRIVATE_COLOR;
        			tsvdata[i].m_color = PRIVATE_COLOR;
    			}
    			else 
    			{
        			tsvdata[i].f_color = PUBLIC_COLOR;
        			tsvdata[i].m_color = PUBLIC_COLOR;
    			}
            }

            svg.selectAll(".pubpriv_legend").attr("opacity", "100%");
            svg.selectAll(".loc_legend").attr("opacity", "0");
            document.getElementById('color_legend').innerHTML = `
					<h4 class="title">Colors:</h4>
					<span class="legend_item" style="color: #202020;">Public</span>, 
					<span class="legend_item" style="color: #B074E8;"> Private</span>
            `;
    	}

    	// If coloring by region
    	else if (this.value == "loc")
    	{
    		for (var i=0; i<tsvdata.length; i++){
    			color = REGION_COLORS[tsvdata[i].census_region];
    			tsvdata[i].f_color = color;
            	tsvdata[i].m_color = color;
            }

            svg.selectAll(".pubpriv_legend").attr("opacity", "0");
            svg.selectAll(".loc_legend").attr("opacity", "100%");
            document.getElementById('color_legend').innerHTML = `
					<h4 class="title">Colors:</h4>
					<span class="legend_item" style="color: #077187;">Northeast</span>, 
					<span class="legend_item" style="color: #CCA43B;"> South</span>,
					<span class="legend_item" style="color: #AB4ADB;"> Midwest</span>,
					<span class="legend_item" style="color: #5BBA6F;"> West</span>,
					<span class="legend_item" style="color: #DB3A34;"> Canada</span>
            `;
    	}

    	// If using default colors 
    	else
    	{
    		for (var i=0; i<tsvdata.length; i++){
    			tsvdata[i].f_color = DEFAULT_F_COLOR;
            	tsvdata[i].m_color = DEFAULT_M_COLOR;
            }	

            f_marker_color = DEFAULT_F_COLOR;
            m_marker_color = DEFAULT_M_COLOR;
            svg.selectAll(".pubpriv_legend").attr("opacity", "0");
            svg.selectAll(".loc_legend").attr("opacity", "0");
            document.getElementById('color_legend').innerHTML = ``;
    	}

    	// Update the legend colors
    	svg.selectAll(".f_marker").attr("stroke", f_marker_color);
        svg.selectAll(".m_marker").attr("stroke", m_marker_color);;

    	// Force redraw.
        rearrange(sortby, true);
	});
</script>

<a name="analysis"></a>
# Preliminary analyses

Parental leave policies are highly variable across universities. Here are a few quick analyses to illustrate some of the patterns.

![Leave durations by gender](python/figures/distribution_by_gender.png)
	Women receive paid parental leave at 120 of 197 institutions, and men at 114 of 197. Women receive longer parental leave than men (38 universities, or 19%). 77 institutions (39%) provide no paid parental leave. 82 institutions (42%) provide some non-zero amount of gender-neutral leave. Averaging over all data, women receive 8.7 weeks, while men receive 6.8 weeks. Only six universities offer paid leave to women but not men, and no universities offer leave to men without offering at least as much leave to women.

![Leave durations by public/private status](python/figures/distribution_by_status.png)
Private institutions provide slightly longer paid parental leaves on average, driven partly by public institutions being twice as likely to offer no paid parental leave at all. If a private institution offers leave, it is typically about one term of leave. Canadian universities also offer significantly more leave than US institutions (see interactive visualization), which reflects the Canadian government's mandate to provide paid leave for new parents (see footnote 1).

![Leave durations by prestige](python/figures/scatter_by_prestige.png)
Using our Computer Science prestige ranking for universities (estimation described [here](http://advances.sciencemag.org/content/1/1/e1400005)), we find that parental leave and prestige exhibit a weak but complicated relationship. Overall, there is a slight positive correlation–more paid leave at more prestigious universities–but the effect size is modest, and the trend appears to reverse for the top 80 or so institutions. These observations suggest that the relationship between parental leave and prestige is complex and will require a level of care and analysis that goes beyond the scope of this blog post. We want to emphasize that these correlations should not be interpreted yet as causal of anything. Understanding the impacts of parental leave and other institutional policies on scientific careers, though, represents an interesting and important topic for future research, and we believe this dataset should help facilitate progress in that direction.

# Conclusions and future directions

This dataset is a building block that can be refined, extended, and incorporated into research on the science of science, and the information can help inform individuals comparing offers from different universities. Parental leave is just one of the many forms of support that institutions can provide to their employees, and achieving a greater understanding of how these and similar policies affect individuals would serve to enhance career experiences both within science and beyond.

Inferring such causal effects from our dataset will require it to be extended in one of several possible ways. First, it would be useful to know when policies were adopted and potentially how they changed over time. Knowing the history of these policies would make it possible to monitor changes in, for example, an institution's retention or recruitment of faculty before and after the adoption of the policy in order to assess its impact, as Antecol et al. did.

Our analysis above suggests a complicated relationship between the prestige of an institution and the duration of its parental leave policy. Part of that complication might arise from the nature of our measurement of prestige, which is derived from faculty placement power in the field of computer science. A university-level measure of prestige, rather than a field-specific measure, may provide more useful insights. For instance, how does the size of an institution's endowment translate into benefits for individual faculty? 

We hope that this blog post is thought provoking for faculty across institutions, and in particular, useful to new faculty navigating their institution’s parental leave policies. Feel free to explore this data set further and contact us with any questions or concerns (facultystudy@colorado.edu). 

# About us

Our research group studies the structure and dynamics of the academic workforce. In the past, we’ve investigated patterns in [faculty hiring outcomes](http://advances.sciencemag.org/content/1/1/e1400005), [researcher productivity](http://www.pnas.org/content/114/44/E9216), [gender's effects on scientific careers](https://arxiv.org/abs/1602.00795), and [faculty retention and promotion](https://arxiv.org/abs/1804.02760). We're located at the University of Colorado at Boulder and the Santa Fe Institute.

* [Aaron Clauset](http://tuvalu.santafe.edu/~aaronc/)
* [Mirta Galesic](https://www.santafe.edu/people/profile/mirta-galesic)
* [Dan Larremore](http://danlarremore.com/)
* [Allie Morgan](https://allisonmorgan.github.io/)
* [Sam Way](http://samfway.com/)

# Footnotes

1. Unpaid parental leave is federally mandated of all US ([FMLA](https://en.wikipedia.org/wiki/Family_and_Medical_Leave_Act_of_1993)) institutions. The Canadian government mandates unpaid leave of employers and offers partial financial support during leave, even if employer doesn’t ([EI](https://www.canada.ca/en/services/benefits/ei/ei-maternity-parental.html)).
2. By this we mean, assistant, associate, or full professors. See [“Academic tenure in North America”](https://en.wikipedia.org/wiki/Academic_tenure_in_North_America).
3. A few institutions lack policies for parental leave and instead refer faculty to apply for medical or disability leave. We coded these institutions as not guaranteeing paid parental leave to faculty, given the absence of a specific policy. Maternity leave, on the other hand, was coded as parental leave.
